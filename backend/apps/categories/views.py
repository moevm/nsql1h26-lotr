"""
Views for category endpoints.

Pattern (analytics style):
  - Thin view classes, logic in services, OpenAPI decorations in openapi.py.
"""

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .openapi import (
    detail_view_schema,
    list_create_view_schema,
    tree_view_schema,
)
from .serializers import (
    CategoryCreateInputSerializer,
    CategoryUpdateInputSerializer,
)


@list_create_view_schema
class CategoryListCreateView(APIView):
    '''GET /categories/ (list) and POST /categories/ (create).'''

    permission_classes = [AllowAny]

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return super().get_permissions()

    def get(self, request: Request) -> Response:
        result = services.list_categories(
            raw_page=request.query_params.get('page'),
            raw_page_size=request.query_params.get('page_size'),
            raw_name=request.query_params.get('name'),
            raw_parent=request.query_params.get('parent'),
            raw_sort=request.query_params.get('sort'),
            raw_order=request.query_params.get('order'),
        )

        base = request.build_absolute_uri('/api/v1/categories/')
        page_size = int(request.query_params.get('page_size', 20))

        def _url(page_num):
            return f'{base}?page={page_num}&page_size={page_size}'

        result['next'] = _url(result['next']) if result['next'] else None
        result['previous'] = _url(result['previous']) if result['previous'] else None

        return Response(result)

    def post(self, request: Request) -> Response:
        if not getattr(request.user, 'is_admin', False):
            return Response(
                {
                    'error': {
                        'code': 'FORBIDDEN',
                        'message': 'Admin role required.',
                    }
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = CategoryCreateInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        created = services.create_category(
            slug=data.get('slug'),
            name=data['name'],
            parent_slug=data.get('parent_slug'),
        )
        return Response(created, status=status.HTTP_201_CREATED)


@tree_view_schema
class CategoryTreeView(APIView):
    '''GET /categories/tree/'''

    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        root = request.query_params.get('root', None)
        tree = services.get_category_tree(root=root)
        return Response(tree)


@detail_view_schema
class CategoryDetailView(APIView):
    '''GET /categories/{slug}/ (detail), PATCH, DELETE.'''

    permission_classes = [AllowAny]

    def get_permissions(self):
        if self.request.method in ('PATCH', 'DELETE'):
            return [IsAuthenticated()]
        return super().get_permissions()

    def get(self, request: Request, slug: str) -> Response:
        detail = services.get_category_detail(
            slug=slug,
            raw_page=request.query_params.get('page'),
            raw_page_size=request.query_params.get('page_size'),
            raw_types=request.query_params.get('types'),
            raw_sort=request.query_params.get('sort'),
        )

        page_size = int(request.query_params.get('page_size', 20))
        base = request.build_absolute_uri(f'/api/v1/categories/{slug}/')

        def _page_url(page_num):
            if page_num is None:
                return None
            params = f'page={page_num}&page_size={page_size}'
            types = request.query_params.get('types')
            if types:
                params += f'&types={types}'
            sort = request.query_params.get('sort')
            if sort:
                params += f'&sort={sort}'
            return f'{base}?{params}'

        detail['pages']['next'] = _page_url(detail['pages']['next'])
        detail['pages']['previous'] = _page_url(detail['pages']['previous'])

        return Response(detail)

    def patch(self, request: Request, slug: str) -> Response:
        if not getattr(request.user, 'is_admin', False):
            return Response(
                {
                    'error': {
                        'code': 'FORBIDDEN',
                        'message': 'Admin role required.',
                    }
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = CategoryUpdateInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        updated = services.update_category(
            slug=slug,
            name=data.get('name'),
            parent_slug=data.get('parent_slug'),
        )
        return Response(updated)

    def delete(self, request: Request, slug: str) -> Response:
        if not getattr(request.user, 'is_admin', False):
            return Response(
                {
                    'error': {
                        'code': 'FORBIDDEN',
                        'message': 'Admin role required.',
                    }
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        services.delete_category(slug)
        return Response(status=status.HTTP_204_NO_CONTENT)
