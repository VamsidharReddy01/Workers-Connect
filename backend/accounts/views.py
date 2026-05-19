from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.throttling import AnonRateThrottle
from rest_framework.response import Response
from rest_framework import status
from .serializers import SignupSerializer, LoginSerializer
from rest_framework_simplejwt.tokens import RefreshToken


class LoginRateThrottle(AnonRateThrottle):
    """Stricter throttle for login attempts to prevent brute-force attacks."""
    rate = '5/minute'


@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):

    serializer = SignupSerializer(data=request.data)

    if serializer.is_valid():
        user = serializer.save()

        # Return tokens immediately so the user is logged in after signup
        refresh = RefreshToken.for_user(user)

        return Response({
            'message': 'User created successfully',
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
            }
        }, status=status.HTTP_201_CREATED)

    return Response(
        {'errors': serializer.errors},
        status=status.HTTP_400_BAD_REQUEST
    )


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([LoginRateThrottle])
def login(request):

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
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
        }
    }, status=status.HTTP_200_OK)