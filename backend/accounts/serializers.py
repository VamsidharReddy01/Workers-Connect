from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from .models import SupportTicket, User


def _absolute_media_url(obj, request):
    if not obj:
        return None
    if request is not None:
        return request.build_absolute_uri(obj.url)
    return obj.url


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
            'profile_photo',
            'profile_photo_url',
        ]
        read_only_fields = ['id', 'role']
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
        fields = ['username', 'email', 'password', 'role', 'phone_number', 'location', 'email_otp']
        extra_kwargs = {
            'role': {'required': False},
            'phone_number': {'required': False},
            'location': {'required': False},
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

    def validate(self, attrs):
        email = attrs.get('email', '').lower()
        otp = attrs.get('email_otp')
        cached_otp = cache.get(f'signup_email_otp:{email}')

        if cached_otp is None:
            raise serializers.ValidationError(
                {'email_otp': 'OTP expired or not requested. Please send a new OTP.'}
            )

        if str(cached_otp) != str(otp):
            raise serializers.ValidationError({'email_otp': 'Invalid OTP.'})

        return attrs

    def create(self, validated_data):
        validated_data.pop('email_otp', None)
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            role=validated_data.get('role', 'customer'),
            phone_number=validated_data.get('phone_number'),
            location=validated_data.get('location'),
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
