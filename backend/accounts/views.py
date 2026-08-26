import logging
import secrets

from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils import timezone
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
from accounts.services.geocoding import forward_geocode, reverse_geocode

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

        try:
            send_mail(
                subject='Workers Bridge signup OTP',
                message=f'Your Workers Bridge signup OTP is {otp}. It expires in 10 minutes.',
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception as exc:
            logger.error('Failed to send OTP email to %s: %s', email, exc)
            return Response(
                {'error': 'Failed to send OTP email. Please check the email server configuration or try again later.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
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
                'Signup success user=%s email=%s role=%s ip=%s',
                user.username, user.email, user.role, _get_client_ip(request),
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


class WorkerSignupView(APIView):
    """
    API View to handle worker registration specifically.
    Guarantees role='worker' and creates WorkerProfile.
    """
    permission_classes = [AllowAny]
    throttle_classes = [SignupRateThrottle]

    def post(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        data['role'] = 'worker'
        serializer = SignupSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            cache.delete(f'signup_email_otp:{user.email.lower()}')
            cache.delete(f'signup_otp_attempts:{user.email.lower()}')
            refresh = RefreshToken.for_user(user)

            security_logger.info(
                'Worker signup success user=%s email=%s ip=%s',
                user.username, user.email, _get_client_ip(request),
            )

            return Response({
                'message': 'Worker account created successfully',
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)

        return Response(
            {'errors': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )


class CustomerSignupView(APIView):
    """
    API View to handle customer registration specifically.
    Guarantees role='customer'.
    """
    permission_classes = [AllowAny]
    throttle_classes = [SignupRateThrottle]

    def post(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        data['role'] = 'customer'
        serializer = SignupSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            cache.delete(f'signup_email_otp:{user.email.lower()}')
            cache.delete(f'signup_otp_attempts:{user.email.lower()}')
            refresh = RefreshToken.for_user(user)

            security_logger.info(
                'Customer signup success user=%s email=%s ip=%s',
                user.username, user.email, _get_client_ip(request),
            )

            return Response({
                'message': 'Customer account created successfully',
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


class GeocodeLookupView(APIView):
    """
    Public endpoint for geocode lookups during registration.
    Accepts latitude+longitude for reverse geocoding or location_name for forward geocoding.
    Rate-limited to prevent abuse.
    """
    permission_classes = [AllowAny]
    throttle_classes = [SignupOtpRateThrottle]  # Reuse existing rate limiter

    def post(self, request, *args, **kwargs):
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        location_name = (request.data.get('location_name') or '').strip()

        # Reverse geocode: coordinates → address
        if latitude is not None and longitude is not None:
            try:
                lat = float(latitude)
                lon = float(longitude)
            except (TypeError, ValueError):
                return Response(
                    {'error': 'Invalid coordinate values.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                return Response(
                    {'error': 'Coordinates out of range.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            result = reverse_geocode(lat, lon)
            if result:
                return Response(result, status=status.HTTP_200_OK)
            return Response(
                {'error': 'Could not resolve address from coordinates.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Forward geocode: address → coordinates
        if location_name:
            result = forward_geocode(location_name)
            if result:
                return Response(result, status=status.HTTP_200_OK)
            return Response(
                {'error': 'Could not resolve coordinates from location name.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {'error': 'Provide latitude+longitude or location_name.'},
            status=status.HTTP_400_BAD_REQUEST,
        )


class UpdateLocationView(APIView):
    """
    Authenticated endpoint to update the current user's location.
    Performs server-side geocoding (reverse for GPS, forward for manual).
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        user = request.user
        location_source = (request.data.get('location_source') or '').strip()
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        location_name = (request.data.get('location_name') or '').strip()

        if location_source not in ('gps', 'manual', ''):
            return Response(
                {'error': 'location_source must be "gps" or "manual".'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # GPS flow
        if location_source == 'gps' or (latitude is not None and longitude is not None):
            if latitude is None or longitude is None:
                return Response(
                    {'error': 'Latitude and longitude are required for GPS location.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                lat = float(latitude)
                lon = float(longitude)
            except (TypeError, ValueError):
                return Response(
                    {'error': 'Invalid coordinate values.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                return Response(
                    {'error': 'Coordinates out of range.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            resolved_name = location_name
            if not resolved_name:
                geo_result = reverse_geocode(lat, lon)
                if geo_result:
                    resolved_name = geo_result.get('location_name', '')

            user.latitude = lat
            user.longitude = lon
            user.location = resolved_name or user.location or ''
            user.location_source = 'gps'
            user.location_permission_granted = True
            user.location_updated_at = timezone.now()
            user.save(update_fields=[
                'latitude', 'longitude', 'location', 'location_source',
                'location_permission_granted', 'location_updated_at',
            ])

            security_logger.info(
                'Location updated (GPS) user=%s ip=%s',
                user.username, _get_client_ip(request),
            )

            return Response({
                'latitude': float(user.latitude),
                'longitude': float(user.longitude),
                'location_name': user.location,
                'location_source': user.location_source,
            }, status=status.HTTP_200_OK)

        # Manual flow
        if location_name:
            user.location = location_name
            user.location_source = 'manual'

            geo_result = forward_geocode(location_name)
            if geo_result:
                user.latitude = geo_result.get('latitude')
                user.longitude = geo_result.get('longitude')
                resolved_name = geo_result.get('location_name')
                if resolved_name:
                    user.location = resolved_name
            else:
                user.latitude = None
                user.longitude = None

            user.location_updated_at = timezone.now()
            user.save(update_fields=[
                'latitude', 'longitude', 'location', 'location_source',
                'location_updated_at',
            ])

            security_logger.info(
                'Location updated (manual) user=%s ip=%s',
                user.username, _get_client_ip(request),
            )

            return Response({
                'latitude': float(user.latitude) if user.latitude else None,
                'longitude': float(user.longitude) if user.longitude else None,
                'location_name': user.location,
                'location_source': user.location_source,
            }, status=status.HTTP_200_OK)

        return Response(
            {'error': 'Provide latitude+longitude or location_name.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
