import logging
import secrets

from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.throttling import AnonRateThrottle
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    SignupSerializer,
    SupportTicketSerializer,
    UserSerializer,
)

# SECURITY FIX #21: Dedicated security logger for audit trail
security_logger = logging.getLogger('security')
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
# OTP configuration from environment
# ──────────────────────────────────────────────────────────────

OTP_EXPIRY_SECONDS = int(getattr(settings, 'SIGNUP_OTP_EXPIRY_SECONDS', 600))
OTP_MAX_VERIFY_ATTEMPTS = int(getattr(settings, 'SIGNUP_OTP_MAX_VERIFY_ATTEMPTS', 5))


def _get_client_ip(request):
    """Extract client IP for audit logging."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'unknown')


# ──────────────────────────────────────────────────────────────
# Throttle classes
# ──────────────────────────────────────────────────────────────

class LoginRateThrottle(AnonRateThrottle):
    """Limit login attempts to prevent brute-force attacks."""

    def get_rate(self):
        return getattr(settings, 'LOGIN_THROTTLE_RATE', '5/minute')


class SignupOtpRateThrottle(AnonRateThrottle):
    """Limit signup OTP requests."""

    def get_rate(self):
        return getattr(settings, 'SIGNUP_OTP_THROTTLE_RATE', '3/minute')


class SignupRateThrottle(AnonRateThrottle):
    """SECURITY FIX #10: Rate limit signup to prevent OTP brute-force."""

    def get_rate(self):
        return getattr(settings, 'SIGNUP_THROTTLE_RATE', '10/minute')



# ──────────────────────────────────────────────────────────────
# Views
# ──────────────────────────────────────────────────────────────

class SendSignupOtpView(APIView):
    """
    Sends a short-lived OTP to the email address used on the signup page.
    """
    permission_classes = [AllowAny]
    throttle_classes = [SignupOtpRateThrottle]

    def post(self, request, *args, **kwargs):
        email = (request.data.get('email') or '').strip().lower()

        if not email:
            return Response(
                {'errors': {'email': ['Email is required.']}},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            validate_email(email)
        except ValidationError:
            return Response(
                {'errors': {'email': ['Enter a valid email address.']}},
                status=status.HTTP_400_BAD_REQUEST
            )

        # SECURITY FIX #11: Do NOT reveal whether the email is already registered.
        # Always return the same generic success message.
        if User.objects.filter(email__iexact=email).exists():
            # Log the attempt but return the same response as success
            security_logger.info(
                'OTP requested for existing email=%s ip=%s',
                email, _get_client_ip(request),
            )
            return Response(
                {'message': 'If this email is eligible, an OTP has been sent.'},
                status=status.HTTP_200_OK
            )

        # SECURITY FIX #3: Use cryptographically secure random for OTP
        otp = f'{secrets.randbelow(1000000):06d}'
        cache.set(f'signup_email_otp:{email}', otp, timeout=OTP_EXPIRY_SECONDS)
        # SECURITY FIX #10: Reset attempt counter when new OTP is generated
        cache.set(f'signup_otp_attempts:{email}', 0, timeout=OTP_EXPIRY_SECONDS)

        send_mail(
            subject='Workers Bridge signup OTP',
            message=f'Your Workers Bridge signup OTP is {otp}. It expires in 10 minutes.',
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
            recipient_list=[email],
            fail_silently=False,
        )

        security_logger.info(
            'OTP sent to email=%s ip=%s',
            email, _get_client_ip(request),
        )

        return Response(
            {'message': 'If this email is eligible, an OTP has been sent.'},
            status=status.HTTP_200_OK
        )


class SignupView(APIView):
    """
    API View to handle user registration.
    """
    permission_classes = [AllowAny]
    # SECURITY FIX #10: Rate limit signup endpoint
    throttle_classes = [SignupRateThrottle]

    def post(self, request, *args, **kwargs):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Clean up OTP and attempt counter from cache
            cache.delete(f'signup_email_otp:{user.email.lower()}')
            cache.delete(f'signup_otp_attempts:{user.email.lower()}')
            refresh = RefreshToken.for_user(user)

            security_logger.info(
                'Signup success user=%s email=%s ip=%s',
                user.username, user.email, _get_client_ip(request),
            )

            return Response({
                'message': 'User created successfully',
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)

        return Response(
            {'errors': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )


class LoginView(APIView):
    """
    API View to handle user login.
    """
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            # SECURITY FIX #21: Log failed login attempts
            email = request.data.get('email', 'unknown')
            security_logger.warning(
                'Login failed email=%s ip=%s',
                email, _get_client_ip(request),
            )
            return Response(
                {'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)

        # SECURITY FIX #21: Log successful login
        security_logger.info(
            'Login success user=%s email=%s ip=%s',
            user.username, user.email, _get_client_ip(request),
        )

        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)


class UserProfileView(APIView):
    """
    API View to retrieve and update the authenticated user's profile details.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get(self, request, *args, **kwargs):
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                UserSerializer(request.user, context={'request': request}).data,
                status=status.HTTP_200_OK,
            )
        return Response(
            {'errors': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    def put(self, request, *args, **kwargs):
        serializer = UserSerializer(request.user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                UserSerializer(request.user, context={'request': request}).data,
                status=status.HTTP_200_OK,
            )
        return Response(
            {'errors': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request},
        )
        if serializer.is_valid():
            serializer.save()
            # SECURITY FIX #21: Log password change
            security_logger.info(
                'Password changed user=%s ip=%s',
                request.user.username, _get_client_ip(request),
            )
            return Response(
                {'message': 'Password changed successfully.'},
                status=status.HTTP_200_OK,
            )
        return Response(
            {'errors': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class SupportTicketListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        tickets = request.user.support_tickets.all()
        serializer = SupportTicketSerializer(tickets, many=True)
        return Response({'list': serializer.data}, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = SupportTicketSerializer(data=request.data)
        if serializer.is_valid():
            ticket = serializer.save(user=request.user)
            return Response(
                SupportTicketSerializer(ticket).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {'errors': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class LogoutView(APIView):
    """
    API View to logout a user by invalidating the refresh token.
    If 'rest_framework_simplejwt.token_blacklist' is enabled, the refresh token will be blacklisted.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response(
                    {"error": "Refresh token is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            token = RefreshToken(refresh_token)
            # If token blacklisting is installed and configured in settings, blacklist it
            try:
                token.blacklist()
            except AttributeError:
                # Blacklist app is not installed, so client-side clearing is sufficient
                pass

            # Deactivate the specific device token if provided, otherwise deactivate all
            fcm_token = (request.data.get('fcm_token') or '').strip()
            try:
                from notifications.models import DeviceToken
                if fcm_token:
                    DeviceToken.objects.filter(user=request.user, token=fcm_token).update(is_active=False)
                else:
                    DeviceToken.objects.filter(user=request.user).update(is_active=False)
            except Exception as exc:
                logger.debug('Device token deactivation skipped: %s', exc)

            # SECURITY FIX #21: Log logout
            security_logger.info(
                'Logout user=%s ip=%s',
                request.user.username, _get_client_ip(request),
            )

            return Response(
                {"message": "Logged out successfully"},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": "Invalid token or error during logout"},
                status=status.HTTP_400_BAD_REQUEST
            )
