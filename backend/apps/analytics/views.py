
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializer import (
    GlobalStatsSerializer,
    NeighborsResponseSerializer,
    ShortestPathResponseSerializer,
)
from .services import global_stats, neighbors, shortest_path

_SLUG_PARAM = OpenApiParameter(
    name='slug',
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=True,
    description='Slug of the root wiki page.',
)

_THROUGH_NODES_PARAM = OpenApiParameter(
    name='through_nodes',
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=False,
    description=(
        'Comma-separated entity types allowed on the traversal path '
        '(e.g. `character,location`).  Applies to ALL non-root nodes '
        'on the path, not just the final endpoint.  '
        'Omit to allow all node types.'
    ),
)

_THROUGH_RELS_PARAM = OpenApiParameter(
    name='through_rels',
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=False,
    description=(
        'Comma-separated relationship types to include in the edge result '
        '(e.g. `OF_RACE,BORN_IN`).  Case-insensitive.  '
        'Omit to include all relationship types.'
    ),
)

_DEPTH_PARAM = OpenApiParameter(
    name="depth",
    type=OpenApiTypes.INT,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Traversal depth.  Must be 1 or 2.  Defaults to 1.",
    enum=[1, 2],
)

_LIMIT_PARAM = OpenApiParameter(
    name="limit",
    type=OpenApiTypes.INT,
    location=OpenApiParameter.QUERY,
    required=False,
    description=(
        "Maximum number of neighbour nodes to return.  "
        "Defaults to 100, maximum 1000."
    ),
)

_FROM_PARAM = OpenApiParameter(
    name='from',
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=True,
    description='Slug of the start page.',
)

_TO_PARAM = OpenApiParameter(
    name='to',
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=True,
    description='Slug of the end page.  Must differ from `from`.',
)

_MAX_DEPTH_PARAM = OpenApiParameter(
    name='max_depth',
    type=OpenApiTypes.INT,
    location=OpenApiParameter.QUERY,
    required=False,
    description='Maximum number of hops to explore.  Default 10, maximum 15.',
)


class GlobalStatsView(APIView):
    '''
    GET /api/v1/analytics/global

    Returns aggregated statistics for the entire LotR wiki graph.
    Public.
    Results are cached for 5 minutes server-side.
    '''

    permission_classes = [AllowAny]

    @extend_schema(
        summary='Global wiki statistics',
        description=(
            'Returns aggregated statistics for the entire LotR wiki graph: '
            'entity counts, character breakdowns, engagement metrics, and '
            'most-connected nodes.  Results are cached server-side for 5 minutes.'
        ),
        tags=['analytics'],
        responses={200: GlobalStatsSerializer},
        auth=[],
    )
    def get(self, request: Request) -> Response:  # noqa: ARG002
        return Response(global_stats())


class NeighborsView(APIView):
    '''
    GET /api/v1/analytics/neighbors/

    Returns the neighbour subgraph for a given wiki page.
    Public. Not cached.
    '''

    permission_classes = [AllowAny]

    @extend_schema(
        summary='Node neighbours graph',
        description=(
            'Returns the subgraph of :Page nodes reachable from `slug` within '
            '`depth` hops, together with the induced set of directed lore edges '
            'connecting them.'
            'Use `through_nodes` and `through_rels` to restrict which types of '
            'nodes / edges appear in the result.  Both accept comma-separated values '
            'and default to "all" when omitted.\n\n'
        ),
        tags=['analytics'],
        parameters=[
            _SLUG_PARAM,
            _THROUGH_NODES_PARAM,
            _THROUGH_RELS_PARAM,
            _DEPTH_PARAM,
            _LIMIT_PARAM,
        ],
        responses={
            200: NeighborsResponseSerializer,
            400: None,
            404: None,
        },
        auth=[],
    )
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

    @extend_schema(
        summary='Shortest path between two wiki pages',
        description=(
            'Returns the shortest lore path between `from` and `to` page '
            'slugs using Neo4j\'s `shortestPath()` algorithm.\n\n'
            '**Filter semantics:**\n'
            '- `through_nodes` — every non-endpoint node on the path must '
            'carry one of these entity-type labels.\n'
            '- `through_rels` — every relationship on the path must be of one '
            'of these types; otherwise the path is rejected (`found: false`).\n\n'
            '**Known limitation:** if the absolute shortest path violates a filter, '
            'a longer path that satisfies it is NOT returned.  This is a trade-off '
            'inherent to Neo4j\'s `shortestPath()` implementation.'
        ),
        tags=['analytics'],
        parameters=[
            _FROM_PARAM,
            _TO_PARAM,
            _THROUGH_NODES_PARAM,
            _THROUGH_RELS_PARAM,
            _MAX_DEPTH_PARAM,
        ],
        responses={
            200: ShortestPathResponseSerializer,
            400: None,
            404: None,
        },
        auth=[],
    )
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
