from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from .models import User
from .serializers import (
    AuthResponseSerializer,
    AuthUserSerializer,
    CustomTokenObtainPairSerializer,
    LogoutSerializer,
    MePatchSerializer,
    MeSerializer,
    RegisterSerializer,
    TokenPairSerializer,
)
from .services import get_liked_pages

# Swagger schema for /me response (includes likedPages from service)

_ME_RESPONSE_SCHEMA = inline_serializer(
    name='MeResponse',
    fields={
        'username': serializers.CharField(read_only=True),
        'email': serializers.EmailField(read_only=True),
        'first_name': serializers.CharField(read_only=True),
        'last_name': serializers.CharField(read_only=True),
        'role': serializers.CharField(read_only=True),
        'avatar_url': serializers.URLField(read_only=True, allow_null=True),
        'likedPages': serializers.ListField(
            child=serializers.DictField(
                child=serializers.CharField(allow_null=True)
            ),
            read_only=True,
        ),
    }
)


# Helper functions

def _build_me_response(user: User) -> dict:
    data = MeSerializer(user).data
    data['likedPages'] = get_liked_pages(user.id)

    return data


class RegisterView(APIView):
    '''
    POST /auth/register/
    Creates a new user with role='viewer' and issues JWT pair immediately.
    Public endpoint
    '''

    permission_classes = [AllowAny]

    @extend_schema(
        tags=['auth'],
        summary='Register a new user',
        request=RegisterSerializer,
        responses={201: AuthResponseSerializer}
    )
    def post(self, request: Request) -> Response:
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()
        refresh = CustomTokenObtainPairSerializer.get_token(user)
        response_data = {
            'user': AuthUserSerializer(user).data,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
        }

        return Response(response_data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=['auth'],
    summary='Login - obtain JWT token pair',
    request=CustomTokenObtainPairSerializer,
    responses={200: AuthResponseSerializer},
)
class LoginView(TokenObtainPairView):
    '''
    POST /auth/login
    Returns {user, tokens} - validate() in serializer builds the shape
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
    TODO: see if we can cast it to some other error type so we don't have to do
    anythin manually
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
    PATCH /auth/me/ - update profile (role is read_only), return same shape
    '''

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['auth'],
        summary='Get current user profile',
        responses={200: _ME_RESPONSE_SCHEMA},
    )
    def get(self, request: Request) -> Response:
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        user: User = request.user  # type: ignore[assignment]
        return Response(_build_me_response(user))

    @extend_schema(
        tags=['auth'],
        summary='Update current user profile',
        request=MePatchSerializer,
        responses={200: _ME_RESPONSE_SCHEMA},
    )
    def patch(self, request: Request) -> Response:
        serializer = MePatchSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        return Response(_build_me_response(user))
