'''
View for GET /api/v1/search/.

Public endpoint — no authentication required.
'''

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .queries import VALID_TYPES
from .serializers import SearchQuerySerializer, SearchResultSerializer
from .services import search


class SearchView(APIView):
    '''
    GET /api/v1/search/

    Fulltext search across all wiki entities.
    Intended for navbar autocomplete and analytics entity picker.

    Results are ordered by relevance score.
    '''

    permission_classes = [AllowAny]

    @extend_schema(
        summary='Global fulltext search',
        description=(
            'Searches the `names` property of all entity types using a Neo4j '
            'fulltext index.  Results are ordered by relevance.  '
            'Designed for autocomplete — prefix matching is applied to each '
            'token ("frod" matches "Frodo Baggins").  Multi-word queries '
            'use AND semantics: "ring bear" matches "Ring-bearer".'
        ),
        tags=['search'],
        parameters=[
            OpenApiParameter(
                name='q',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=True,
                description='Search query (minimum 2 characters).',
            ),
            OpenApiParameter(
                name='types',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description=(
                    f'Comma-separated entity types to restrict results to. '
                    f'Valid: {", ".join(sorted(VALID_TYPES))}.'
                ),
            ),
            OpenApiParameter(
                name='limit',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Maximum number of results (1-20, default 5).',
            ),
        ],
        responses={
            200: SearchResultSerializer(many=True),
            400: OpenApiTypes.OBJECT,
        },
        auth=[],
    )
    def get(self, request: Request) -> Response:
        params = SearchQuerySerializer(data=request.query_params)
        params.is_valid(raise_exception=True)

        results = search(
            q=params.validated_data['q'],
            raw_types=params.validated_data['types'],
            limit=params.validated_data['limit'],
        )
        return Response(results)
