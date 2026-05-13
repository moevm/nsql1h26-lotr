
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .openapi import (
    custom_analytics_view_schema,
    global_stats_view_schema,
    neighbors_view_schema,
    shortest_path_view_schema,
)
from .serializers import (
    CustomAnalyticsGroupedSerializer,
    CustomAnalyticsSimpleSerializer,
)
from .services import custom_analytics, global_stats, neighbors, shortest_path


class GlobalStatsView(APIView):
    '''
    GET /api/v1/analytics/global

    Returns aggregated statistics for the entire LotR wiki graph.
    Public.
    Results are cached for 5 minutes server-side.
    '''

    permission_classes = [AllowAny]

    @global_stats_view_schema
    def get(self, request: Request) -> Response:  # noqa: ARG002
        return Response(global_stats())


class NeighborsView(APIView):
    '''
    GET /api/v1/analytics/neighbors/

    Returns the neighbour subgraph for a given wiki page.
    Public. Not cached.
    '''

    permission_classes = [AllowAny]

    @neighbors_view_schema
    def get(self, request: Request) -> Response:
        slug = request.query_params.get('slug', '').strip()

        if not slug:
            raise ValidationError({'slug': ['This field is required']})

        return Response(neighbors(
            slug=slug,
            raw_through_nodes=request.query_params.get('through_nodes'),
            raw_through_rels=request.query_params.get('through_rels'),
            raw_depth=request.query_params.get('depth'),
            raw_limit=request.query_params.get('limit'),
        ))


class ShortestPathView(APIView):
    '''
    GET /api/v1/analytics/shortest-path/

    Finds the shortest lore path between two wiki pages.

    Public, no authentication.
    '''

    permission_classes = [AllowAny]

    @shortest_path_view_schema
    def get(self, request: Request) -> Response:
        raw_from = request.query_params.get('from', '').strip()
        raw_to = request.query_params.get('to', '').strip()

        errors: dict[str, list[str]] = {}
        if not raw_from:
            errors['from'] = ['This field is required.']
        if not raw_to:
            errors['to'] = ['This field is required.']
        if errors:
            raise ValidationError(errors)

        return Response(shortest_path(
            raw_from=raw_from,
            raw_to=raw_to,
            raw_through_nodes=request.query_params.get('through_nodes'),
            raw_through_rels=request.query_params.get('through_rels'),
            raw_max_depth=request.query_params.get('max_depth'),
        ))


class CustomAnalyticsView(APIView):
    '''
    GET /api/v1/analytics/custom/

    Return histogram data for a chosen entity type and attribute.
    '''

    permission_classes = [AllowAny]

    @custom_analytics_view_schema
    def get(self, request: Request) -> Response:
        params = dict(request.query_params)
        flat_params = {
            k: v[0] if isinstance(v, list) and v else v for k, v in params.items()
        }

        result = custom_analytics(
            raw_entity_type=flat_params.get('entity_type'),
            raw_attr=flat_params.get('attr'),
            raw_group_by=flat_params.get('group_by'),
            raw_top_n=flat_params.get('top_n'),
            query_params=flat_params,
        )

        if result.get('group_by') is None:
            serializer = CustomAnalyticsSimpleSerializer
        else:
            serializer = CustomAnalyticsGroupedSerializer

        return Response(serializer(result).data)
