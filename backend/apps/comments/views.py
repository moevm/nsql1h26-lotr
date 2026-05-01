'''
Permission model:
    GET: AllowAny  (unauthenticated users can read comments)
    POST: IsAuthenticated  (any logged-in user, viewer or admin)
    DELETE: IsAuthenticated  (ownership enforced in service layer)
    PATCH: IsAuthenticated  (ownership enforced in service layer)
'''

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    inline_serializer,
)
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

# TODO: move into apps.core or something
from apps.catalogs.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE

from .serializers import CommentInputSerializer, CommentOutputSerializer
from .services import create_comment, delete_comment, list_comments, update_comment

# Shared schema helpers

_SLUG_PARAM = OpenApiParameter(
    'slug',
    OpenApiTypes.STR,
    OpenApiParameter.PATH,
    description='Page slug.',
)

_ID_PARAM = OpenApiParameter(
    'id',
    OpenApiTypes.STR,
    OpenApiParameter.PATH,
    description=(
        'Neo4j element ID of the comment (string). ' \
        'Obtained from the `id` field of a Comment object.'
    ),
)

_PAGINATED_COMMENTS = inline_serializer(
    name='PaginatedCommentList',
    fields={
        'count': serializers.IntegerField(),
        'next': serializers.CharField(
            allow_null=True,
            help_text='Next page number or null',
        ),
        'previous': serializers.CharField(
            allow_null=True,
            help_text='Previous page number or null',
        ),
        'results': CommentOutputSerializer(many=True),
    },
)


# Helpers

def _parse_int(value: str | None, default: int) -> int:
    try:
        return int(value) if value is not None else default
    except (ValueError, TypeError):
        return default


# TODO: remove dublication with apps/catalogs/services.py::_build_pagination_urls
def _build_pagination_urls(
    request: Request,
    slug: str,
    next_page: int | None,
    previous_page: int | None,
    page_size: int,
) -> tuple[str | None, str | None]:
    '''Build full absolute URLs for next/previous pagination links.'''
    base = request.build_absolute_uri(f'/api/v1/pages/{slug}/comments/')

    def _url(p: int) -> str:
        return f'{base}?page={p}&page_size={page_size}'

    return (
        _url(next_page) if next_page else None,
        _url(previous_page) if previous_page else None,
    )


# Views

class CommentListCreateView(APIView):
    '''
    GET /api/v1/pages/{slug}/comments/ - list comments (public)
    POST /api/v1/pages/{slug}/comments/ - create comment [authenticated]
    '''

    def get_permissions(self) -> list:
        if self.request.method == 'GET':
            return [AllowAny()]

        return [IsAuthenticated()]

    @extend_schema(
        summary='List comments for a page',
        description=(
            'Returns a paginated list of comments for the given page, '
            'ordered by creation time (oldest first). Public endpoint.'
        ),
        tags=['pages'],
        parameters=[
            _SLUG_PARAM,
            OpenApiParameter(
                'page',
                OpenApiTypes.INT,
                description='Page number (default: 1)'
            ),
            OpenApiParameter(
                'page_size',
                OpenApiTypes.INT,
                description='Items per page (default: 20, max: 100)',
            ),
        ],
        responses={
            200: _PAGINATED_COMMENTS,
            404: OpenApiTypes.OBJECT,
        },
        auth=[],
    )
    def get(self, request: Request, slug: str) -> Response:
        page = max(1, _parse_int(request.query_params.get('page'), 1))
        page_size = min(
            MAX_PAGE_SIZE,
            max(1, _parse_int(request.query_params.get('page_size'), DEFAULT_PAGE_SIZE))
        )

        result = list_comments(slug=slug, page=page, page_size=page_size)

        next_url, prev_url = _build_pagination_urls(
            request,
            slug,
            result['next'],
            result['previous'],
            page_size,
        )
        result['next'] = next_url
        result['previous'] = prev_url

        return Response(result)

    @extend_schema(
        summary='Add a comment to a page',
        description=(
            'Creates a comment on the given page. '
            'Requires authentication (viewer or admin role).'
        ),
        tags=['pages'],
        parameters=[_SLUG_PARAM],
        request=CommentInputSerializer,
        responses={
            201: CommentOutputSerializer,
            400: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
    )
    def post(self, request: Request, slug: str) -> Response:
        serializer = CommentInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        comment = create_comment(
            slug=slug,
            text=serializer.validated_data['text'],
            requesting_django_id=request.user.id,
        )

        return Response(comment, status=status.HTTP_201_CREATED)

class CommentDetailView(APIView):
    '''
    DELETE /api/v1/pages/{slug}/comments/{id}/ - delete comment
    PATCH /api/v1/pages/{slug}/comments/{id}/ - update comment's text

    - viewer: only own comment.
    - admin: delete any comment.
    '''

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Delete a comment',
        description=(
            'Deletes a comment. '
            'Viewers may only delete their own comments; '
            'admins may delete any comment.'
        ),
        tags=['pages'],
        parameters=[_SLUG_PARAM, _ID_PARAM],
        responses={
            204: OpenApiResponse(description='Comment deleted successfully.'),
            401: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
    )
    def delete(self, request: Request, slug: str, comment_id: str) -> Response:
        delete_comment(
            slug=slug,
            comment_id=comment_id,
            requesting_django_id=request.user.id,
            is_admin=getattr(request.user, 'is_admin', False),
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        summary='Update comment text',
        description='Update comment\'s text. Only its author',
        tags=['pages'],
        parameters=[_SLUG_PARAM, _ID_PARAM],
        request=CommentInputSerializer,
        responses={
            200: CommentOutputSerializer,
            400: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
    )
    def patch(self, request: Request, slug: str, comment_id: str) -> Response:
        serializer = CommentInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated = update_comment(
            slug=slug,
            comment_id=comment_id,
            text=serializer.validated_data['text'],
            requesting_django_id=request.user.id,
        )
        return Response(updated, status=status.HTTP_200_OK)
