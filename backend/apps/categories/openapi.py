'''
OpenAPI schema descriptors for the categories endpoints.
'''

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)

from .serializers import (
    CategoryCreateInputSerializer,
    CategoryDetailOutputSerializer,
    CategoryTreeItemSerializer,
    CategoryUpdateInputSerializer,
    PaginatedCategoryListSerializer,
)

_PAGE_PARAM = OpenApiParameter(
    name='page',
    type=OpenApiTypes.INT,
    location=OpenApiParameter.QUERY,
    required=False,
    description='Page number (default: 1).',
)

_PAGE_SIZE_PARAM = OpenApiParameter(
    name='page_size',
    type=OpenApiTypes.INT,
    location=OpenApiParameter.QUERY,
    required=False,
    description='Items per page (default: 20, max: 100).',
)

_NAME_PARAM = OpenApiParameter(
    name='name',
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=False,
    description='Substring match in category name.',
)

_PARENT_PARAM = OpenApiParameter(
    name='parent',
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Parent slug or 'root' for root categories.",
)

_SORT_PARAM = OpenApiParameter(
    name='sort',
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=False,
    description='Sort field (allowed: name).',
)

_ORDER_PARAM = OpenApiParameter(
    name='order',
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=False,
    description='Sort direction: asc (default) or desc.',
)

_ROOT_PARAM = OpenApiParameter(
    name='root',
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=False,
    description='Slug of a root category to return a subtree.',
)

_SLUG_PATH_PARAM = OpenApiParameter(
    'slug',
    OpenApiTypes.STR,
    OpenApiParameter.PATH,
    description='Category slug.',
)

_TYPES_PARAM = OpenApiParameter(
    name='types',
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=False,
    description='Comma-separated page types to filter.',
)

_SORT_DETAIL_PARAM = OpenApiParameter(
    name='sort',
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=False,
    description='Sort field for pages inside category (allowed: name).',
)

list_create_view_schema = extend_schema_view(
    get=extend_schema(
        summary='List categories',
        description=(
            'Returns a paginated flat list of categories with filtering.'
        ),
        tags=['categories'],
        parameters=[
            _PAGE_PARAM,
            _PAGE_SIZE_PARAM,
            _NAME_PARAM,
            _PARENT_PARAM,
            _SORT_PARAM,
            _ORDER_PARAM,
        ],
        responses={200: PaginatedCategoryListSerializer},
        auth=[],
    ),
    post=extend_schema(
        summary='Create a category (admin)',
        description='Creates a new category. Requires admin role.',
        tags=['categories'],
        request=CategoryCreateInputSerializer,
        responses={
            201: CategoryDetailOutputSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
            409: OpenApiTypes.OBJECT,
            422: OpenApiTypes.OBJECT,
        },
    ),
)

tree_view_schema = extend_schema(
    summary='Category tree',
    description=(
        'Returns the full category tree, optionally rooted at a given slug.'
    ),
    tags=['categories'],
    parameters=[_ROOT_PARAM],
    responses={200: CategoryTreeItemSerializer(many=True)},
    auth=[],
)

detail_view_schema = extend_schema_view(
    get=extend_schema(
        summary='Get category detail',
        description=(
            'Returns detailed information about a category, '
            'its parent, children, and paginated pages.'
        ),
        tags=['categories'],
        parameters=[
            _SLUG_PATH_PARAM,
            _PAGE_PARAM,
            _PAGE_SIZE_PARAM,
            _TYPES_PARAM,
            _SORT_DETAIL_PARAM,
        ],
        responses={
            200: CategoryDetailOutputSerializer,
            404: OpenApiTypes.OBJECT,
        },
        auth=[],
    ),
    patch=extend_schema(
        summary='Update a category (admin)',
        description='Update category name or parent. Only admin.',
        tags=['categories'],
        parameters=[_SLUG_PATH_PARAM],
        request=CategoryUpdateInputSerializer,
        responses={
            200: CategoryDetailOutputSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
            422: OpenApiTypes.OBJECT,
        },
    ),
    delete=extend_schema(
        summary='Delete a category (admin)',
        description=(
            'Deletes the category. Child categories become root.'
        ),
        tags=['categories'],
        parameters=[_SLUG_PATH_PARAM],
        responses={
            204: OpenApiResponse(description='Category deleted.'),
            404: OpenApiTypes.OBJECT,
        },
    ),
)
