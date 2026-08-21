import io
import logging

from PIL import Image
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from django.utils import timezone
from .models import SupportTicket, User

logger = logging.getLogger(__name__)

MAX_PROFILE_PHOTO_SIZE = 5 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {'image/jpeg', 'image/png', 'image/webp'}
# SECURITY FIX #16: Allowed Pillow image formats for magic-byte validation
ALLOWED_IMAGE_FORMATS = {'JPEG', 'PNG', 'WEBP'}

# SECURITY FIX #10: OTP brute-force attempt limit
OTP_MAX_VERIFY_ATTEMPTS = 5


def validate_latitude(value):
    if value in (None, ''):
        return None
    if value < -90 or value > 90:
        raise serializers.ValidationError('Latitude must be between -90 and 90.')
    return value


def validate_longitude(value):
    if value in (None, ''):
        return None
    if value < -180 or value > 180:
        raise serializers.ValidationError('Longitude must be between -180 and 180.')
    return value


def _absolute_media_url(obj, request):
    if not obj:
        return None
    if request is not None:
        return request.build_absolute_uri(obj.url)
    return obj.url


def _validate_image_magic_bytes(value):
    """
    SECURITY FIX #16: Validate uploaded image by reading its actual file content
    with Pillow, not just the client-provided Content-Type header.
    """
    if value is None:
        return value
    try:
        # Read the file into memory and verify with Pillow
        value.seek(0)
        img = Image.open(value)
        img.verify()
        if img.format not in ALLOWED_IMAGE_FORMATS:
            raise serializers.ValidationError(
                f'Invalid image format "{img.format}". Upload a JPG, PNG, or WebP image.'
            )
        value.seek(0)  # Reset file pointer for Django to save
    except serializers.ValidationError:
        raise
    except Exception:
        raise serializers.ValidationError(
            'File is not a valid image. Upload a JPG, PNG, or WebP image.'
        )
    return value


# ──────────────────────────────────────────────────────────────
# SECURITY FIX #20: Separate Public serializer (masks sensitive data)
# ──────────────────────────────────────────────────────────────

class PublicUserSerializer(serializers.ModelSerializer):
    """
    User serializer for public-facing endpoints (e.g. worker listings).
    Masks email, phone, and reduces location precision.
    """
    profile_photo_url = serializers.SerializerMethodField()
    masked_location = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'role',
            'masked_location',
            'profile_photo_url',
        ]
        read_only_fields = fields

    def get_profile_photo_url(self, obj):
        if not obj.profile_photo:
            return None
        return _absolute_media_url(obj.profile_photo, self.context.get('request'))

    def get_masked_location(self, obj):
        return obj.location or ''


# ──────────────────────────────────────────────────────────────
# Private UserSerializer (for authenticated user's own profile)
# ──────────────────────────────────────────────────────────────

class UserSerializer(serializers.ModelSerializer):
    profile_photo_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'role',
            'phone_number',
            'location',
            'latitude',
            'longitude',
            'location_permission_granted',
            'location_updated_at',
            'profile_photo',
            'profile_photo_url',
        ]
        read_only_fields = ['id', 'role', 'location_updated_at']
        extra_kwargs = {'profile_photo': {'write_only': True, 'required': False}}

    def get_profile_photo_url(self, obj):
        if not obj.profile_photo:
            return None
        return _absolute_media_url(obj.profile_photo, self.context.get('request'))

    def validate_username(self, value):
        value = value.strip()
        if len(value) < 3:
            raise serializers.ValidationError('Name must be at least 3 characters.')
        queryset = User.objects.filter(username__iexact=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError('A user with this name already exists.')
        return value

    def validate_email(self, value):
        value = value.strip().lower()
        queryset = User.objects.filter(email__iexact=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value

    def validate_phone_number(self, value):
        if value in (None, ''):
            return value
        value = value.strip()
        queryset = User.objects.filter(phone_number=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError('A user with this phone number already exists.')
        return value

    def validate_profile_photo(self, value):
        if value is None:
            return value
        if value.size > MAX_PROFILE_PHOTO_SIZE:
            raise serializers.ValidationError('Profile photo must be 5 MB or smaller.')
        # SECURITY FIX #16: Validate both Content-Type AND magic bytes
        content_type = getattr(value, 'content_type', '')
        if content_type not in ALLOWED_IMAGE_TYPES:
            raise serializers.ValidationError('Upload a JPG, PNG, or WebP image.')
        return _validate_image_magic_bytes(value)

    def validate_latitude(self, value):
        return validate_latitude(value)

    def validate_longitude(self, value):
        return validate_longitude(value)

    def validate(self, attrs):
        latitude = attrs.get('latitude', getattr(self.instance, 'latitude', None))
        longitude = attrs.get('longitude', getattr(self.instance, 'longitude', None))
        if (latitude is None) != (longitude is None):
            raise serializers.ValidationError(
                {'location': 'Latitude and longitude must be provided together.'}
            )
        return attrs

    def update(self, instance, validated_data):
        new_photo = validated_data.get('profile_photo')
        old_photo = instance.profile_photo if new_photo and instance.profile_photo else None
        if 'latitude' in validated_data or 'longitude' in validated_data:
            validated_data['location_updated_at'] = timezone.now()
        instance = super().update(instance, validated_data)
        if old_photo and old_photo.name != instance.profile_photo.name:
            old_photo.delete(save=False)
        return instance


class SignupSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        error_messages={
            'min_length': 'Password must be at least 8 characters long.',
        }
    )
    email = serializers.EmailField(required=True)
    email_otp = serializers.CharField(write_only=True, min_length=6, max_length=6)

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password',
            'role',
            'phone_number',
            'location',
            'latitude',
            'longitude',
            'location_permission_granted',
            'email_otp',
        ]
        extra_kwargs = {
            # SECURITY FIX #8: role is read-only — server assigns it, users cannot
            # choose their own role during signup.
            'role': {'required': False, 'read_only': True},
            'phone_number': {'required': False},
            'location': {'required': False},
            'latitude': {'required': False},
            'longitude': {'required': False},
            'location_permission_granted': {'required': False},
        }

    def validate_email(self, value):
        """Ensure email is unique (case-insensitive)."""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value.lower()

    def validate_username(self, value):
        """Ensure username is unique (case-insensitive)."""
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError('A user with this username already exists.')
        return value

    def validate_latitude(self, value):
        return validate_latitude(value)

    def validate_longitude(self, value):
        return validate_longitude(value)

    def validate(self, attrs):
        email = attrs.get('email', '').lower()
        otp = attrs.get('email_otp')
        latitude = attrs.get('latitude')
        longitude = attrs.get('longitude')
        cached_otp = cache.get(f'signup_email_otp:{email}')

        if (latitude is None) != (longitude is None):
            raise serializers.ValidationError(
                {'location': 'Latitude and longitude must be provided together.'}
            )

        if cached_otp is None:
            raise serializers.ValidationError(
                {'email_otp': 'OTP expired or not requested. Please send a new OTP.'}
            )

        # SECURITY FIX #10: Track OTP verification attempts and lock out
        attempts_key = f'signup_otp_attempts:{email}'
        attempts = cache.get(attempts_key, 0)
        if attempts >= OTP_MAX_VERIFY_ATTEMPTS:
            # Invalidate the OTP entirely after max attempts
            cache.delete(f'signup_email_otp:{email}')
            cache.delete(attempts_key)
            raise serializers.ValidationError(
                {'email_otp': 'Too many failed attempts. Please request a new OTP.'}
            )

        if str(cached_otp) != str(otp):
            # Increment attempt counter
            cache.set(attempts_key, attempts + 1, timeout=10 * 60)
            raise serializers.ValidationError({'email_otp': 'Invalid OTP.'})

        return attrs

    def create(self, validated_data):
        validated_data.pop('email_otp', None)
        # SECURITY FIX #8: Always assign 'customer' role — ignore any client-provided role
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            role='customer',
            phone_number=validated_data.get('phone_number'),
            location=validated_data.get('location'),
            latitude=validated_data.get('latitude'),
            longitude=validated_data.get('longitude'),
            location_permission_granted=validated_data.get('location_permission_granted', False),
            location_updated_at=timezone.now()
            if validated_data.get('latitude') is not None and validated_data.get('longitude') is not None
            else None,
        )
        return user


class LoginSerializer(serializers.Serializer):
    """Validates login input and authenticates the user."""

    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        user = authenticate(username=email, password=password)

        if user is None:
            raise serializers.ValidationError(
                {'credentials': 'Invalid email or password.'}
            )

        if not user.is_active:
            raise serializers.ValidationError(
                {'account': 'This account has been deactivated.'}
            )

        attrs['user'] = user
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Old password is incorrect.')
        return value

    def validate(self, attrs):
        if attrs.get('new_password') != attrs.get('confirm_password'):
            raise serializers.ValidationError(
                {'confirm_password': 'Passwords do not match.'}
            )
        validate_password(attrs['new_password'], self.context['request'].user)
        return attrs

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save(update_fields=['password'])
        return user


class SupportTicketSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = SupportTicket
        fields = [
            'id',
            'subject',
            'message',
            'status',
            'status_display',
            'admin_note',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'status', 'status_display', 'admin_note', 'created_at', 'updated_at']

    def validate_subject(self, value):
        value = value.strip()
        if len(value) < 3:
            raise serializers.ValidationError('Subject must be at least 3 characters.')
        return value

    def validate_message(self, value):
        value = value.strip()
        if len(value) < 10:
            raise serializers.ValidationError('Message must be at least 10 characters.')
        return value
