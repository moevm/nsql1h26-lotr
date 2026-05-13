'''
Layers note:
    No Cypher and no db import. Repository!! Yay!!!

Global stats note:
    The bulk import endpoint must call invalidate_global_stats_cache() after a
    successful import so the next request recomputes fresh numbers.
'''

from collections import Counter, defaultdict
from typing import Any

from django.conf import settings
from django.core.cache import cache
from rest_framework.exceptions import NotFound, ValidationError

from apps.catalogs.filters import build_filter_from_params
from apps.pages.enums import RelType
from apps.pages.queries import LABEL_TO_TYPE, labels_to_type

from .constants import (
    CUSTOM_ANALYTICS_TOP_N_DEFAULT,
    CUSTOM_ANALYTICS_TOP_N_MAX,
    NEIGHBORS_ALLOWED_DEPTHS,
    NEIGHBORS_DEFAULT_LIMIT,
    NEIGHBORS_MAX_LIMIT,
    SHORTEST_PATH_DEFAULT_MAX_DEPTH,
    SHORTEST_PATH_MAX_ALLOWED_DEPTH,
    SHORTEST_PATH_MIN_DEPTH,
)
from .queries import ATTR_DEFS
from .repository import (
    CustomAnalyticsRepositoryProtocol,
    GlobalStatsRepositoryProtocol,
    GroupedHistogramRow,
    NeighborsRepositoryProtocol,
    Neo4jCustomAnalyticsRepository,
    Neo4jGlobalStatsRepository,
    Neo4jNeighborsRepository,
    Neo4jShortestPathRepository,
    PageRow,
    ShortestPathRepositoryProtocol,
    ShortestPathResult,
    SimpleHistogramRow,
)

GLOBAL_STATS_CACHE_KEY = 'analytics:global_stats'

_VALID_ENTITY_TYPES: frozenset[str] = frozenset(LABEL_TO_TYPE.values())
_TYPE_TO_LABEL: dict[str, str] = {v: k for k, v in LABEL_TO_TYPE.items()}
_VALID_REL_TYPES: frozenset[str] = frozenset(RelType)

# Module-level default repository instances
# Views call the public service functions without specifying a repo.
# Tests override via the keyword-only `repo` argument.

_default_global_stats_repo: GlobalStatsRepositoryProtocol = Neo4jGlobalStatsRepository()
_default_neighbors_repo: NeighborsRepositoryProtocol = Neo4jNeighborsRepository()
_default_shortest_path_repo: ShortestPathRepositoryProtocol = Neo4jShortestPathRepository()
_default_custom_analytics_repo: CustomAnalyticsRepositoryProtocol = Neo4jCustomAnalyticsRepository()


def _assemble(repo: GlobalStatsRepositoryProtocol) -> dict[str, Any]:
    '''
    Call every repository method and assemble the response dict.

    Kept separate from global_stats() so it is testable without the cache
    getting in the way.
    '''
    return {
        'counts': repo.get_counts(),
        'characters_by_race': repo.get_characters_by_race(),
        'characters_by_gender': repo.get_characters_by_gender(),
        'is_alive_stats': repo.get_characters_by_is_alive(),
        'events_by_timeline': repo.get_events_by_timeline(),
        'locations_by_type': repo.get_locations_by_type(),
        'items_by_type': repo.get_items_by_type(),
        'top_connected': repo.get_top_connected(),
        'most_liked': repo.get_most_liked(),
        'most_commented': repo.get_most_commented(),
    }


def _page_summary(row: PageRow) -> dict[str, Any]:
    '''Build a minimal page representation from a PageRow'''
    entity_type = labels_to_type(row.node_labels)

    return {
        'slug': row.slug,
        'type': entity_type or 'unknown',
        'name': row.names[0] if row.names else None,
        'image_url': row.image_url,
    }


def _parse_bounded_int(
    raw: str | None,
    field: str,
    default: int,
    min_val: int,
    max_val: int,
) -> int:
    '''
    Parse a raw query-param string to a bounded integer.

    Centralises the try/except + range-check pattern that would otherwise
    be duplicated in every integer query-param parser.
    '''
    if raw is None:
        return default

    try:
        value = int(raw)
    except (ValueError, TypeError) as exc:
        raise ValidationError(
            {
                field: ["Must be an integer."],
            },
        ) from exc

    if value < min_val or value > max_val:
        raise ValidationError(
            {
                field: [f'Must be between {min_val} and {max_val}.']
            }
        )

    return value


def _parse_node_types(raw: str | None) -> list[str] | None:
    '''
    Parse and validate the `through_nodes` query parameter.

    Accepts a comma-separated list of entity type strings.
    Returns None when absent (all node types).
    '''
    if not raw or not raw.strip():
        return None

    requested = [t.strip() for t in raw.split(',') if t.strip()]
    if not requested:
        return None

    invalid = sorted(set(requested) - _VALID_ENTITY_TYPES)
    if invalid:
        raise ValidationError(
            {
                'through_nodes': [
                    f'Invalid type(s): {", ".join(invalid)}. '
                    f'Allowed: {", ".join(sorted(_VALID_ENTITY_TYPES))}'
                ]
            }
        )

    return [_TYPE_TO_LABEL[t] for t in requested]


def _parse_rel_types(raw: str | None) -> list[str] | None:
    '''
    Parse and validate the `through_rels` query parameter.

    Values are normalised to upper-case before validation so callers may
    send "born_in" or "BORN_IN" interchangeably.
    Returns None when absent (all relationship types).
    '''
    if not raw or not raw.strip():
        return None

    rel_types = [rt.strip().upper() for rt in raw.split(',') if rt.strip()]

    invalid = sorted(set(rel_types) - _VALID_REL_TYPES)
    if invalid:
        raise ValidationError(
            {
                'through_rels': [
                    f'Invalid relationship type(s): {", ".join(invalid)}. '
                    f'Allowed: {", ".join(sorted(_VALID_REL_TYPES))}'
                ]
            }
        )

    return rel_types


def _parse_depth(raw: str | None) -> int:
    '''
    Parse the `depth` parameter.  Allowed: 1 or 2.  Default: 1.
    '''
    value = _parse_bounded_int(raw, 'depth', default=1, min_val=1, max_val=2)

    if value not in NEIGHBORS_ALLOWED_DEPTHS:
        raise ValidationError({'depth': ['Must be 1 or 2.']})

    return value


def _parse_limit(raw: str | None) -> int:
    '''Parse the ``limit`` parameter.  Default: 100, max: 1000.'''
    return _parse_bounded_int(
        raw,
        'limit',
        default=NEIGHBORS_DEFAULT_LIMIT,
        min_val=1,
        max_val=NEIGHBORS_MAX_LIMIT,
    )


def _parse_max_depth(raw: str | None) -> int:
    '''Parse the `max_depth` parameter. Default: 10, max: 15'''
    return _parse_bounded_int(
        raw,
        'max_depth',
        default=SHORTEST_PATH_DEFAULT_MAX_DEPTH,
        min_val=SHORTEST_PATH_MIN_DEPTH,
        max_val=SHORTEST_PATH_MAX_ALLOWED_DEPTH,
    )


_SUPPORTED_ENTITY_TYPES: frozenset[str] = frozenset(ATTR_DEFS.keys())
_ANALYTICS_PARAMS = frozenset({'entity_type', 'attr', 'group_by', 'top_n'})


def _validate_entity_type(entity_type: str) -> None:
    if entity_type not in _SUPPORTED_ENTITY_TYPES:
        raise ValidationError({
            'entity_type': [
                f'"{entity_type}" is not supported for custom analytics. '
                f'Supported: {", ".join(sorted(_SUPPORTED_ENTITY_TYPES))}.'
            ]
        })


def _validate_attr(entity_type: str, attr: str, param_name: str = 'attr') -> None:
    allowed = ATTR_DEFS.get(entity_type, {})
    if attr not in allowed:
        raise ValidationError({
            param_name: [
                f'"{attr}" is not a valid attribute for entity_type="{entity_type}". '
                f'Allowed: {", ".join(sorted(allowed))}.'
            ]
        })


def _validate_group_by(entity_type: str, attr: str, group_by: str) -> None:
    _validate_attr(entity_type, group_by, param_name='group_by')

    if group_by == attr:
        raise ValidationError({
            'group_by': [f'"group_by" must differ from "attr" ("{attr}").']
        })

    attr_def = ATTR_DEFS[entity_type][attr]
    group_def = ATTR_DEFS[entity_type][group_by]

    if attr_def.is_rel and group_def.is_rel:
        raise ValidationError({
            'group_by': [
                f'Both attr="{attr}" and group_by="{group_by}" require '
                f'relationship traversal.  Two REL-mode attributes together '
                f'produce a Cartesian product and make count() semantically '
                f'incorrect.  Use a PROP or BOOL attribute for group_by.'
            ]
        })


def _parse_top_n(raw: str | None) -> int:
    if raw is None:
        return CUSTOM_ANALYTICS_TOP_N_DEFAULT

    try:
        value = int(raw)
    except (ValueError, TypeError) as exc:
        raise ValidationError({
            'top_n': ['Must be an integer.']
        }) from exc

    if not (1 <= value <= CUSTOM_ANALYTICS_TOP_N_MAX):
        raise ValidationError({
            'top_n': [f'Must be between 1 and {CUSTOM_ANALYTICS_TOP_N_MAX}.']
        })

    return value


def _make_simple_response(
    entity_type: str,
    attr: str,
    rows: list[SimpleHistogramRow],
) -> dict[str, Any]:
    return {
        'entity_type': entity_type,
        'attr': attr,
        'group_by': None,
        'data': [
            {
                'x': r['x'],
                'value': r['value'],
            }
            for r in rows
        ],
    }


def _pivot_grouped(
    rows: list[GroupedHistogramRow],
    top_n: int,
) -> tuple[list[str], list[dict[str, Any]]]:
    '''Pivot flat (x, g, value) rows into stacked-bar format.'''
    counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    all_groups: set[str] = set()

    for row in rows:
        x = str(row['x']) if row['x'] is not None else '(unknown)'
        g = str(row['g']) if row['g'] is not None else '(unknown)'
        counts[x][g] += row['value']
        all_groups.add(g)

    ranked_x = sorted(
        counts.keys(),
        key=lambda x: -sum(counts[x].values()),
    )[:top_n]

    groups = sorted(all_groups)
    data = [
        {'x': x, **{g: counts[x].get(g, 0) for g in groups}}
        for x in ranked_x
    ]

    return groups, data


def _make_grouped_response(
    entity_type: str,
    attr: str,
    group_by: str,
    rows: list[GroupedHistogramRow],
    top_n: int,
) -> dict[str, Any]:
    groups, data = _pivot_grouped(rows, top_n)
    return {
        'entity_type': entity_type,
        'attr': attr,
        'group_by': group_by,
        'groups': groups,
        'data': data,
    }


# Public API

def global_stats(
        *,
        repo: GlobalStatsRepositoryProtocol = _default_global_stats_repo,
) -> dict[str, Any]:
    '''
    Return aggregated statistics for the entire wiki graph.

    Results are cached for settings.ANALYTICS_GLOBAL_CACHE_TTL seconds
    Call invalidate_global_stats_cache() to clear the cache when the graph changes
    (e.g. after bulk import).
    '''
    cached = cache.get(GLOBAL_STATS_CACHE_KEY)
    if cached is not None:
        return cached

    result = _assemble(repo)
    ttl: int = getattr(settings, 'ANALYTICS_GLOBAL_CACHE_TTL', 300)
    cache.set(GLOBAL_STATS_CACHE_KEY, result, ttl)

    return result


def invalidate_global_stats_cache() -> None:
    '''
    Evict the global stats cache entry.

    Call this from any endpoint that mutates the graph in bulk
    (currently: bulk import).  CRUD operations on individual nodes
    intentionally do NOT call this — the 5-minute TTL is acceptable
    staleness for single-record edits.
    '''
    cache.delete(GLOBAL_STATS_CACHE_KEY)


def neighbors(
    slug: str,
    raw_through_nodes: str | None,
    raw_through_rels: str | None,
    raw_depth: str | None,
    raw_limit: str | None,
    *,
    repo: NeighborsRepositoryProtocol = _default_neighbors_repo,
) -> dict[str, Any]:
    '''
    Return the neighbour subgraph for a wiki page.

    Flow:
        Validate all parameters (400 on bad input, before any DB call).
        Verify the root node exists (404 if not).
        Collect reachable :Page nodes within `depth` hops.
        Fetch the induced subgraph of directed lore edges among all slugs.
        Aggregate stats (by_type, by_relation).
    '''
    node_labels = _parse_node_types(raw_through_nodes)
    rel_types = _parse_rel_types(raw_through_rels)
    depth = _parse_depth(raw_depth)
    limit = _parse_limit(raw_limit)

    root_row = repo.get_root(slug)
    if root_row is None:
        raise NotFound(detail=f'Page with slug {slug} not found.')

    root = _page_summary(root_row)
    nodes = [
        _page_summary(r) for r in repo.get_neighbors(
            slug, depth, node_labels, rel_types, limit
        )
    ]

    all_slugs = [root['slug']] + [n['slug'] for n in nodes]
    edges = [
        {
            "from": e.from_slug,
            "to": e.to_slug,
            "type": e.rel_type,
            "properties": e.rel_properties,
        }
        for e in repo.get_induced_edges(all_slugs, rel_types)
    ]

    by_type = dict(Counter(str(node['type']) for node in nodes))
    by_relation = dict(Counter(str(edge['type']) for edge in edges))

    return {
        'root_node': root,
        'nodes': nodes,
        'edges': edges,
        'stats': {
            'total_neighbors': len(nodes),
            'by_type': by_type,
            'by_relation': by_relation,
        },
    }


def shortest_path(
        raw_from: str,
        raw_to: str,
        raw_through_nodes: str | None,
        raw_through_rels: str | None,
        raw_max_depth: str | None,
        *,
        repo: ShortestPathRepositoryProtocol = _default_shortest_path_repo,
) -> dict[str, Any]:
    '''
    Find and return the shortest lore path between two wiki pages.

    Flow:
        Validate all parameters (400 on bad input).
        Reject from_slug == to_slug (400).
        Verify both endpoint nodes exist (404 if either missing).
        Run the shortestPath Cypher query.
        Not found -> {found: false}.
        Found -> enrich path nodes with image_url, build step chain.

    shortestPath() caveat:
        If the absolute shortest path violates through_nodes/through_rels
        filters, the query returns nothing — it does NOT try the next-shortest
        valid path.  Known Neo4j behaviour; document in the UI if needed.
    '''
    from_slug = raw_from.strip()
    to_slug = raw_to.strip()
    node_labels = _parse_node_types(raw_through_nodes)
    rel_types = _parse_rel_types(raw_through_rels)
    max_depth = _parse_max_depth(raw_max_depth)

    if from_slug == to_slug:
        raise ValidationError(
            {
                'from': ['"from" and "to" nust be different slugs.']
            }
        )

    from_row = repo.get_page(from_slug)
    if from_row is None:
        raise NotFound(detail=f'Page with slug "{from_slug}" not found.')

    to_row = repo.get_page(to_slug)
    if to_row is None:
        raise NotFound(detail=f'Page with slug "{to_slug}" not found.')

    from_summary = _page_summary(from_row)
    to_summary = _page_summary(to_row)

    result: ShortestPathResult | None = repo.find_shortest_path(
        from_slug=from_slug,
        to_slug=to_slug,
        node_labels=node_labels,
        rel_types=rel_types,
        max_depth=max_depth,
    )

    if result is None:
        return {
            'found': False,
            'length': None,
            'from': from_summary,
            'to': to_summary,
            'path': [],
        }

    path_slugs = [n.slug for n in result.path_nodes]
    image_map = repo.get_pages_images_urls(path_slugs)

    enriched_nodes = [
        _page_summary(
            PageRow(
                slug=n.slug,
                names=n.names,
                node_labels=n.node_labels,
                image_url=image_map.get(n.slug)
            )
        )
        for n in result.path_nodes
    ]

    steps = [
        {
            'node': node_summary,
            'edge_to_next': (
                {
                    'type': result.path_rels[i].rel_type,
                    'properties': result.path_rels[i].rel_properties,
                }
                if i < len(result.path_rels)
                else None
            ),
        }
        for i, node_summary in enumerate(enriched_nodes)
    ]

    return {
        'found': True,
        'length': result.length,
        'from': from_summary,
        'to': to_summary,
        'path': steps,
    }


def custom_analytics(
    raw_entity_type: str | None,
    raw_attr: str | None,
    raw_group_by: str | None,
    raw_top_n: str | None,
    query_params: dict[str, str],
    *,
    repo: CustomAnalyticsRepositoryProtocol = _default_custom_analytics_repo
) -> dict[str, Any]:
    '''Validate inputs, call the repo, and assemble the histogram response.'''
    if not raw_entity_type:
        raise ValidationError({
            'entity_type': ['This field if required']
        })
    if not raw_attr:
        raise ValidationError({
            'attr': ['This field is required.']
        })

    entity_type = raw_entity_type.strip().lower()
    attr = raw_attr.strip().lower()

    _validate_entity_type(entity_type)
    _validate_attr(entity_type, attr)

    group_by: str | None = raw_group_by.strip().lower() if raw_group_by else None
    if group_by:
        _validate_group_by(entity_type, attr, group_by)

    top_n = _parse_top_n(raw_top_n)

    catalog_params = {k: v for k, v in query_params.items() if k not in _ANALYTICS_PARAMS}
    filter_obj = build_filter_from_params(entity_type, catalog_params)
    filter_where, filter_params = filter_obj.to_cypher_where()

    if group_by is None:
        rows = repo.get_simple_histogram(
            entity_type, attr, filter_where, filter_params, top_n
        )
        return _make_simple_response(entity_type, attr, rows)
    else:
        rows = repo.get_grouped_histogram(
            entity_type, attr, group_by, filter_where, filter_params
        )
        return _make_grouped_response(entity_type, attr, group_by, rows, top_n)
