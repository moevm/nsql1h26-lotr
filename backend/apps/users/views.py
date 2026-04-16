from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from drf_spectacular.utils import extend_schema

from apps.users.serializers import (
    RegisterSerializer,
    UserProfileSerializer,
    CustomTokenObtainPairSerializer,
    TokenPairSerializer,
    LogoutSerializer
)


class RegisterView(APIView):
    '''
    POST /auth/register/
    Creates a new user with role='viewer'.
    Public endpoint
    '''

    permission_classes = [AllowAny]

    @extend_schema(
        tags=['auth'],
        summary='Register a new user',
        request=RegisterSerializer,
        responses={201: UserProfileSerializer}
    )
    def post(self, request: Request) -> Response:
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        return Response(
            UserProfileSerializer(user).data,
            status=status.HTTP_201_CREATED
        )


@extend_schema(
    tags=['auth'],
    summary='Login - obtain JWT token pair',
    request=CustomTokenObtainPairSerializer,
    responses={200: TokenPairSerializer},
)
class LoginView(TokenObtainPairView):
    '''
    POST /auth/login
    Returns access and refresh JWT tokens with `role` in payload
    '''

    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]


@extend_schema(
    tags=['auth'],
    summary='Refresh access token',
    responses={200: TokenPairSerializer},
)
class RefreshView(TokenRefreshView):
    '''
    POST /auth/refresh/
    Rotates the refresh token and issues a new pair, old one is blacklisted.
    Rotation is configured in settings.SIMPLE_JWT
    '''

    permission_classes = [AllowAny]


class LogoutView(APIView):
    '''
    POST /auth/logout/
    Blacklists the provided refresh token.

    NB: TokenError is not a DRF APIException, so we have to catch it manually
    '''

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['auth'],
        summary='Logout - blacklist refresh token',
        request=LogoutSerializer,
        responses={204: None}
    )
    def post(self, request: Request) -> Response:
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            token = RefreshToken(serializer.validated_data['refresh'])
            token.blacklist()
        except TokenError as exc:
            return Response(
                {
                    'error': {'code': 'TOKEN_ERROR',
                              'message': str(exc),
                              'fields': None}
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    '''
    GET /auth/me - return current user's profile
    PATCH /auth/me/ - update email, first_name, last_name (role is read_only)
    '''

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['auth'],
        summary='Get current user profile',
        responses={200: UserProfileSerializer},
    )
    def get(self, request: Request) -> Response:
        return Response(UserProfileSerializer(request.user).data)

    @extend_schema(
        tags=['auth'],
        summary='Update current user profile',
        request=UserProfileSerializer,
        responses={200: UserProfileSerializer},
    )
    def patch(self, request: Request) -> Response:
        serializer = UserProfileSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)

        serializer.save()

        return Response(serializer.data)
