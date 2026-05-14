from typing import Any

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.exceptions import PermissionDenied
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

from .constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from .models import User
from .permissions import IsAdminRole
from .serializers import (
    AuthResponseSerializer,
    AuthUserSerializer,
    CustomTokenObtainPairSerializer,
    LogoutSerializer,
    MePatchSerializer,
    MeSerializer,
    PaginatedPageSummarySerializer,
    RegisterSerializer,
    TokenPairSerializer,
    UserAdminListSerializer,
    UserPublicProfileSerializer,
    UserRoleSerializer,
)
from .services import (
    PaginatedResult,
    _build_pagination_urls,
    build_public_profile,
    delete_user_and_cleanup,
    get_liked_pages,
)

# Allowed sort fields for GET /users/ - whitelist prevents sorting by
# arbitrary (potentially sensitive) columns like `password`.
_ALLOWED_USER_SORT_FIELDS: frozenset[str] = frozenset({'username', 'date_joined'})


# Pagination helpers (same logic as catalogs/views.py)
# TODO: DRY
def _parse_int(value: str | None, default: int) -> int:
    try:
        return int(value) if value is not None else default
    except (ValueError, TypeError):
        return default


def _get_pagination_params(request: Request) -> tuple[int, int]:
    page = max(1, _parse_int(request.query_params.get('page'), 1))
    page_size = min(
        MAX_PAGE_SIZE,
        max(1, _parse_int(request.query_params.get('page_size'), DEFAULT_PAGE_SIZE)),
    )
    return page, page_size


def _filter_params_for_pagination(request: Request) -> dict[str, Any]:
    '''All query params except page/page_size - preserved in next/prev URLs.'''
    return {
        k: v
        for k, v in request.query_params.items()
        if k not in ('page', 'page_size')
    }


def _paginated_response(result: PaginatedResult) -> Response:
    return Response({
        'count': result.count,
        'next': result.next,
        'previous': result.previous,
        'results': result.results,
    })


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
    }
)


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
        return Response(MeSerializer(user).data)

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

        return Response(MeSerializer(user).data)


class CurrentUserLikedPagesView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['auth'],
        summary='List pages liked by the current user',
        responses={
            200: PaginatedPageSummarySerializer,
        },
    )
    def get(self, request: Request) -> Response:
        user = request.user
        page, page_size = _get_pagination_params(request)
        filter_params = _filter_params_for_pagination(request)

        result = get_liked_pages(
            django_id=user.pk,
            page=page,
            page_size=page_size,
            base_url=request.build_absolute_uri(request.path),
            filter_params=filter_params,
        )
        return _paginated_response(result)


class UserListView(APIView):
    '''
    GET /users/

    Admin-only paginated list of all users.
    '''

    permission_classes = [IsAdminRole]

    @extend_schema(
        tags=['users'],
        summary='List all users (admin)',
        parameters=[
            # Documented inline rather than via schema to keep serializer clean
        ],
        responses={200: UserAdminListSerializer(many=True)},
    )
    def get(self, request: Request) -> Response:
        qs = User.objects.all()

        if username_filter := request.query_params.get('username'):
            qs = qs.filter(username__icontains=username_filter)

        if role_filter := request.query_params.get('role'):
            qs = qs.filter(role=role_filter)

        sort_key = request.query_params.get('sort', 'username')
        order = request.query_params.get('order', 'asc')

        if sort_key not in _ALLOWED_USER_SORT_FIELDS:
            sort_key = 'username'

        sort_field = f'-{sort_key}' if order == 'desc' else sort_key
        qs = qs.order_by(sort_field)

        page, page_size = _get_pagination_params(request)
        count = qs.count()
        offset = (page - 1) * page_size
        users_page = list(qs[offset:offset + page_size])

        filter_params = _filter_params_for_pagination(request)
        next_url, prev_url = _build_pagination_urls(
            request.build_absolute_uri(request.path),
            filter_params,
            page,
            page_size,
            count,
        )

        return Response({
            'count': count,
            'next': next_url,
            'previous': prev_url,
            'results': UserAdminListSerializer(users_page, many=True).data,
        })


class UserDetailView(APIView):
    '''
    GET /users/{username}/ - public profile (anyone)
    PATCH /users/{username}/ - change role (admin only)
    DELETE /users/{username}/ - delete user + Neo4j cleanup (admin only)
    '''

    def get_permissions(self) -> list:
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminRole()]

    @extend_schema(
        tags=['users'],
        summary='Public user profile',
        responses={
            200: UserPublicProfileSerializer,
            404: None
        },
    )
    def get(self, request: Request, username: str) -> Response:
        user = get_object_or_404(User, username=username)
        profile = build_public_profile(user)
        return Response(profile)

    @extend_schema(
        tags=['users'],
        summary='Change user role (admin)',
        request=UserRoleSerializer,
        responses={
            200: UserAdminListSerializer,
            400: None,
            403: None,
            404: None,
        },
    )
    def patch(self, request: Request, username: str) -> Response:
        # Prevent admins from accidentally demoting themselves
        if request.user.username == username:
            raise PermissionDenied('You cannot change your own role.')

        user = get_object_or_404(User, username=username)

        serializer = UserRoleSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_user = serializer.save()

        return Response(UserAdminListSerializer(updated_user).data)

    @extend_schema(
        tags=['users'],
        summary='Delete a user (admin)',
        responses={
            204: None,
            403: None,
            404: None
        },
    )
    def delete(self, request: Request, username: str) -> Response:
        get_object_or_404(User, username=username)

        requesting_user: User = request.user  # type: ignore[assignment]
        delete_user_and_cleanup(requesting_user, username)

        return Response(status=status.HTTP_204_NO_CONTENT)


class UserLikedPagesView(APIView):
    '''
    GET /users/{username}/liked/

    Public paginated list of pages liked by the given user.
    '''

    permission_classes = [AllowAny]

    @extend_schema(
        tags=['users'],
        summary='Public list of pages liked by this user',
        responses={
            200: PaginatedPageSummarySerializer,
            404: None,
        },
    )
    def get(self, request: Request, username: str) -> Response:
        user = get_object_or_404(User, username=username)

        page, page_size = _get_pagination_params(request)
        filter_params = _filter_params_for_pagination(request)

        result = get_liked_pages(
            django_id=user.pk,
            page=page,
            page_size=page_size,
            base_url=request.build_absolute_uri(request.path),
            filter_params=filter_params,
        )

        return _paginated_response(result)
