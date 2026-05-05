'''
Layers note:
    No Cypther and no db import. Repository!! Yay!!!

Global stats note:
    The bulk import endpoint must call invalidate_global_stats_cache() after a
    successful import so the next request recomputes fresh numbers.
'''

from typing import Any

from django.conf import settings
from django.core.cache import cache
from rest_framework.exceptions import NotFound, ValidationError

from apps.pages.enums import RelType
from apps.pages.queries import LABEL_TO_TYPE, labels_to_type

from .constants import (
    NEIGHBORS_ALLOWED_DEPTHS,
    NEIGHBORS_DEFAULT_LIMIT,
    NEIGHBORS_MAX_LIMIT,
)
from .repository import (
    GlobalStatsRepositoryProtocol,
    NeighborsRepositoryProtocol,
    Neo4jGlobalStatsRepository,
    Neo4jNeighborsRepository,
    PageRow,
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
        raise ValidationError({'depth': ['Must de 1 or 2.']})

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

    # TODO: check if can be simplified by Counter
    by_type: dict[str, int] = {}
    for node in nodes:
        key = str(node['type'])
        by_type[key] = by_type.get(key, 0) + 1

    by_relation: dict[str, int] = {}
    for edge in edges:
        key = str(edge['type'])
        by_relation[key] = by_relation.get(key, 0) + 1

    return {
        'root': root,
        'nodes': nodes,
        'edges': edges,
        'stats': {
            'total_neighbors': len(nodes),
            'by_type': by_type,
            'by_relation': by_relation,
        },
    }
