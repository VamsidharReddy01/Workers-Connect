from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .serializers import SignupSerializer
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken

@api_view(['POST'])
def signup(request):

    serializer = SignupSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
        return Response(
            {'message': 'User created successfully'},
            status=status.HTTP_201_CREATED
        )

    return Response(serializer.errors, status=400)


@api_view(['POST'])
def login(request):

    email = request.data.get('email')
    password = request.data.get('password')

    user = authenticate(username=email, password=password)

    if user is None:
        return Response(
            {'error': 'Invalid credentials'},
            status=400
        )

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
    })