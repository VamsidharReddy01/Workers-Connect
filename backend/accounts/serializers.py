from rest_framework import serializers
from django.contrib.auth import authenticate
from django.core.cache import cache
from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'phone_number', 'location']
        read_only_fields = ['id', 'role']


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
