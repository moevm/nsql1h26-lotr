from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

from neomodel import db  # type: ignore[attr-defined]

from .filters import (
    _HasCypherWhere,
)

from .queries import (
    CHARACTER_LIST_QUERY, CHARACTER_COUNT_QUERY, CHARACTER_CREATE_QUERY,
    CHARACTER_SORT_FIELDS, CHARACTER_DEFAULT_SORT,
    RACE_LIST_QUERY, RACE_COUNT_QUERY, RACE_CREATE_QUERY, RACE_SORT_FIELDS,
    RACE_DEFAULT_SORT,
    LOCATION_LIST_QUERY, LOCATION_COUNT_QUERY, LOCATION_CREATE_QUERY,
    LOCATION_SORT_FIELDS, LOCATION_DEFAULT_SORT,
    EVENT_LIST_QUERY, EVENT_COUNT_QUERY, EVENT_CREATE_QUERY, EVENT_SORT_FIELDS,
    EVENT_DEFAULT_SORT,
    ORGANIZATION_LIST_QUERY, ORGANIZATION_COUNT_QUERY,
    ORGANIZATION_CREATE_QUERY, ORGANIZATION_SORT_FIELDS,
    ORGANIZATION_DEFAULT_SORT,
    TIMELINE_LIST_QUERY, TIMELINE_COUNT_QUERY, TIMELINE_CREATE_QUERY,
    TIMELINE_SORT_FIELDS, TIMELINE_DEFAULT_SORT,
    ITEM_LIST_QUERY, ITEM_COUNT_QUERY, ITEM_CREATE_QUERY, ITEM_SORT_FIELDS,
    ITEM_DEFAULT_SORT,
    LANGUAGE_LIST_QUERY, LANGUAGE_COUNT_QUERY, LANGUAGE_CREATE_QUERY,
    LANGUAGE_SORT_FIELDS, LANGUAGE_DEFAULT_SORT,
    SCRIPT_LIST_QUERY, SCRIPT_COUNT_QUERY, SCRIPT_CREATE_QUERY,
    SCRIPT_SORT_FIELDS, SCRIPT_DEFAULT_SORT,
)


_MAX_PAGE_SIZE: int = 100
_DEFAULT_PAGE_SIZE: int = 20


# Entity config - everything the service needs to work with the type
@dataclass
class EntityConfig:
    list_query: str
    count_query: str
    create_query: str
    sort_fields: dict[str, str]
    default_sort: str


CHARACTER_CONFIG = EntityConfig(
    list_query=CHARACTER_LIST_QUERY,
    count_query=CHARACTER_COUNT_QUERY,
    create_query=CHARACTER_CREATE_QUERY,
    sort_fields=CHARACTER_SORT_FIELDS,
    default_sort=CHARACTER_DEFAULT_SORT,
)

RACE_CONFIG = EntityConfig(
    list_query=RACE_LIST_QUERY,
    count_query=RACE_COUNT_QUERY,
    create_query=RACE_CREATE_QUERY,
    sort_fields=RACE_SORT_FIELDS,
    default_sort=RACE_DEFAULT_SORT,
)

LOCATION_CONFIG = EntityConfig(
    list_query=LOCATION_LIST_QUERY,
    count_query=LOCATION_COUNT_QUERY,
    create_query=LOCATION_CREATE_QUERY,
    sort_fields=LOCATION_SORT_FIELDS,
    default_sort=LOCATION_DEFAULT_SORT,
)

EVENT_CONFIG = EntityConfig(
    list_query=EVENT_LIST_QUERY,
    count_query=EVENT_COUNT_QUERY,
    create_query=EVENT_CREATE_QUERY,
    sort_fields=EVENT_SORT_FIELDS,
    default_sort=EVENT_DEFAULT_SORT,
)

ORGANIZATION_CONFIG = EntityConfig(
    list_query=ORGANIZATION_LIST_QUERY,
    count_query=ORGANIZATION_COUNT_QUERY,
    create_query=ORGANIZATION_CREATE_QUERY,
    sort_fields=ORGANIZATION_SORT_FIELDS,
    default_sort=ORGANIZATION_DEFAULT_SORT,
)

TIMELINE_CONFIG = EntityConfig(
    list_query=TIMELINE_LIST_QUERY,
    count_query=TIMELINE_COUNT_QUERY,
    create_query=TIMELINE_CREATE_QUERY,
    sort_fields=TIMELINE_SORT_FIELDS,
    default_sort=TIMELINE_DEFAULT_SORT,
)

ITEM_CONFIG = EntityConfig(
    list_query=ITEM_LIST_QUERY,
    count_query=ITEM_COUNT_QUERY,
    create_query=ITEM_CREATE_QUERY,
    sort_fields=ITEM_SORT_FIELDS,
    default_sort=ITEM_DEFAULT_SORT,
)

LANGUAGE_CONFIG = EntityConfig(
    list_query=LANGUAGE_LIST_QUERY,
    count_query=LANGUAGE_COUNT_QUERY,
    create_query=LANGUAGE_CREATE_QUERY,
    sort_fields=LANGUAGE_SORT_FIELDS,
    default_sort=LANGUAGE_DEFAULT_SORT,
)

SCRIPT_CONFIG = EntityConfig(
    list_query=SCRIPT_LIST_QUERY,
    count_query=SCRIPT_COUNT_QUERY,
    create_query=SCRIPT_CREATE_QUERY,
    sort_fields=SCRIPT_SORT_FIELDS,
    default_sort=SCRIPT_DEFAULT_SORT,
)


# Data types
@dataclass
class PaginatedResult:
    count: int
    next: str | None
    previous: str | None
    results: list[dict[str, Any]]


# Helper functions

def _build_order_by(
        sort: str | None,
        order: str | None,
        sort_fields: dict[str, str],
        default_sort: str,
) -> str:
    '''
    Safely build ORDER BY from whitelist.
    Never puts user input into query string without processing.
    '''
    direction = 'DESC' if (order or '').lower() == 'desc' else 'ASC'
    cypher_field = sort_fields.get(sort or '')

    if not cypher_field:
        return default_sort

    return f'{cypher_field} {direction}'


def _build_pagination_urls(
        base_url: str,
        filter_params: dict[str, Any],
        page: int,
        page_size: int,
        total: int,
) -> tuple[str | None, str | None]:
    '''Builds URL for next/previous while saving all filters'''
    total_pages = max(1, (total + page_size - 1) // page_size)

    def _url(p: int) -> str:
        params = {**filter_params, 'page': p, 'page_size': page_size}
        return f'{base_url}?{urlencode(params)}'

    next_url = _url(page + 1) if page < total_pages else None
    prev_url = _url(page - 1) if page > 1 else None

    return next_url, prev_url


# Main service functions


def _has_cypher_where(f: Any) -> bool:
    return hasattr(f, 'to_cypher_where') and callable(f.to_cypher_where)


def list_catalog(
        config: EntityConfig,
        filters: _HasCypherWhere,
        page: int,
        page_size: int,
        sort: str | None,
        order: str | None,
        base_url: str,
        filter_params: dict[str, Any],
) -> PaginatedResult:
    '''
    Universal listing for all entity types.
    Two DB queries: one for the data, one for count
    '''

    assert _has_cypher_where(filters), 'filters must implement to_cypher_where'

    page = max(1, page)
    page_size = min(_MAX_PAGE_SIZE, max(1, page_size))

    where, params = filters.to_cypher_where()
    order_by = _build_order_by(
        sort, order, config.sort_fields, config.default_sort
    )

    skip = (page - 1) * page_size
    list_params: dict[str, Any] = {**params, 'skip': skip, 'limit': page_size}

    list_query = config.list_query.format(where=where, order_by=order_by)
    count_query = config.count_query.format(where=where)

    results, meta = db.cypher_query(list_query, list_params)
    count_results, _ = db.cypher_query(count_query, params)

    total = int(count_results[0][0]) if count_results else 0
    items: list[dict[str, Any]] = [dict(zip(meta, row)) for row in results]

    next_url, prev_url = _build_pagination_urls(
        base_url, filter_params, page, page_size, total
    )

    print('DEBUG:', list_query)
    print('DEBUG:', count_query)

    return PaginatedResult(
        count=total,
        next=next_url,
        previous=prev_url,
        results=items
    )


def create_entity(
        config: EntityConfig,
        data: dict[str, Any]
) -> dict[str, Any]:
    '''
    Created Neo4j node using raw CYPHER.
    Raises neo4j.exceptions.ConstraintError if slug is not unique
    '''

    results, meta = db.cypher_query(config.create_query, data)

    if not results:
        raise RuntimeError(
            'CREATE query returned no result - node was not created'
        )

    return dict(zip(meta, results[0]))


def slug_exists(slug: str) -> bool:
    '''Checks if Page node with given slug already exists'''

    results, _ = db.cypher_query(
        "MATCH (p:Page {slug: $slug}) RETURN p.slug LIMIT 1",
        {"slug": slug},
    )

    return bool(results)
