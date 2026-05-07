'''
OpenAPI schema descriptors for the analytics endpoints.

This module centralises every drf-spectacular decorator and parameter
definition used by the analytics views.  Keeping schema configuration
separate from ``views.py`` makes both easier to read and maintain -
views stay focused on request/response logic, while this module
declares **what** the API looks like.
'''


from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

from .serializers import (
    GlobalStatsSerializer,
    NeighborsResponseSerializer,
    ShortestPathResponseSerializer,
)

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


global_stats_view_schema = extend_schema(
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

neighbors_view_schema = extend_schema(
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

shortest_path_view_schema = extend_schema(
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
