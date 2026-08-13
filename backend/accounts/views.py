import random

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


class LoginRateThrottle(AnonRateThrottle):
    """Limit login attempts to prevent brute-force attacks."""
    rate = '5/minute'


class SignupOtpRateThrottle(AnonRateThrottle):
    """Limit signup OTP requests."""
    rate = '3/minute'


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

        if User.objects.filter(email__iexact=email).exists():
            return Response(
                {'errors': {'email': ['A user with this email already exists.']}},
                status=status.HTTP_400_BAD_REQUEST
            )

        otp = f'{random.randint(0, 999999):06d}'
        cache.set(f'signup_email_otp:{email}', otp, timeout=10 * 60)

        send_mail(
            subject='Workers Bridge signup OTP',
            message=f'Your Workers Bridge signup OTP is {otp}. It expires in 10 minutes.',
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
            recipient_list=[email],
            fail_silently=False,
        )

        return Response(
            {'message': 'OTP sent to your email.'},
            status=status.HTTP_200_OK
        )


class SignupView(APIView):
    """
    API View to handle user registration.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            cache.delete(f'signup_email_otp:{user.email.lower()}')
            refresh = RefreshToken.for_user(user)
            
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
            return Response(
                {'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)

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
            except Exception:
                pass  # Device token deactivation is best-effort

            return Response(
                {"message": "Logged out successfully"},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": "Invalid token or error during logout"},
                status=status.HTTP_400_BAD_REQUEST
            )
