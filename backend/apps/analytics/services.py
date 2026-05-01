'''
Global stats note:
    The bulk import endpoint must call invalidate_global_stats_cache() after a
    successful import so the next request recomputes fresh numbers.
'''

from typing import Any

from django.conf import settings
from django.core.cache import cache
from neomodel import db  # type: ignore[attr-defined]

from .queries import (
    CHARACTERS_BY_GENDER_QUERY,
    CHARACTERS_BY_IS_ALIVE_COUNT_QUERY,
    CHARACTERS_BY_RACE_QUERY,
    COUNTS_QUERY,
    EVENTS_BY_TIMELINE_QUERY,
    ITEMS_BY_TYPE_QUERY,
    LOCATIONS_BY_TYPE_QUERY,
    MOST_COMMENTED_QUERY,
    MOST_LIKED_QUERY,
    TOP_CONNECTED_LABELS,
    top_connected_query,
)

GLOBAL_STATS_CACHE_KEY = 'analytics:global_stats'


# Internal helpers

def _rows_to_dicts(rows: list, meta: list[str]) -> list[dict[str, Any]]:
    return [dict(zip(meta, row, strict=True)) for row in rows]


def _entity_type_from_labels(labels: list[str]) -> str:
    for label in labels:
        if label != 'Page':
            return label.lower()

    return 'unknown'


def _compute_global_stats_counts() -> dict[str, int]:
    count_rows, count_meta = db.cypher_query(COUNTS_QUERY, {})
    if not count_rows:
        return {
            'total': 0,
            'characters': 0, 'races': 0, 'locations': 0,
            'events': 0, 'organizations': 0, 'timelines': 0,
            'items': 0, 'languages': 0, 'scripts': 0,
        }

    row = dict(zip(count_meta, count_rows[0], strict=True))
    counts = {
        'characters': int(row.get('characters', 0)),
        'races': int(row.get('races', 0)),
        'locations': int(row.get('locations', 0)),
        'events': int(row.get('events', 0)),
        'organizations': int(row.get('organizations', 0)),
        'timelines': int(row.get('timelines', 0)),
        'items': int(row.get('items', 0)),
        'languages': int(row.get('languages', 0)),
        'scripts': int(row.get('scripts', 0)),
    }
    counts['total'] = sum(counts.values())
    return counts


def _compute_global_stats_character_by_race() -> list[dict[str, Any]]:
    race_rows, race_meta = db.cypher_query(CHARACTERS_BY_RACE_QUERY, {})
    characters_by_race = [
        {
            'slug': r['slug'],
            'name': r['name'],
            'count': int(r['count']),
        }
        for r in _rows_to_dicts(race_rows, race_meta)
    ]

    return characters_by_race


def _compute_global_stats_characters_by_gender() -> list[dict[str, Any]]:
    gender_rows, gender_meta = db.cypher_query(CHARACTERS_BY_GENDER_QUERY, {})
    characters_by_gender = [
        {
            'gender': r['gender'],
            'count': int(r['count']),
        }
        for r in _rows_to_dicts(gender_rows, gender_meta)
    ]

    return characters_by_gender

def _compute_global_stats_character_by_is_alive() -> dict[str, int]:
    alive_rows, alive_meta = db.cypher_query(CHARACTERS_BY_IS_ALIVE_COUNT_QUERY, {})
    alive_row = dict(zip(alive_meta, alive_rows[0], strict=True)) if alive_rows else {}
    is_alive_stats = {
        'alive': int(alive_row.get('alive', 0)),
        'deceased': int(alive_row.get('deceased', 0)),
    }

    return is_alive_stats


def _compute_global_stats_events_by_timeline() -> list[dict[str, Any]]:
    tl_rows, tl_meta = db.cypher_query(EVENTS_BY_TIMELINE_QUERY, {})
    events_by_timeline = [
        {
            'timeline_slug': r['timeline_slug'],
            'name': r['name'],
            'count': int(r['count']),
        }
        for r in _rows_to_dicts(tl_rows, tl_meta)
    ]

    return events_by_timeline


def _compute_global_stats_locations_by_type() -> list[dict[str, Any]]:
    loc_rows, loc_meta = db.cypher_query(LOCATIONS_BY_TYPE_QUERY, {})
    locations_by_type = [
        {
            'type': r['type'],
            'count': int(r['count']),
        }
        for r in _rows_to_dicts(loc_rows, loc_meta)
    ]

    return locations_by_type


def _compute_global_stats_items_by_type() -> list[dict[str, Any]]:
    item_rows, item_meta = db.cypher_query(ITEMS_BY_TYPE_QUERY, {})
    items_by_type = [
        {
            'type': r['type'],
            'count': int(r['count']),
        }
        for r in _rows_to_dicts(item_rows, item_meta)
    ]

    return items_by_type


def _compute_global_stats_top_connected() -> dict[str, list[dict[str, Any]]]:
    top_connected: dict[str, list[dict[str, Any]]] = {}
    for label in TOP_CONNECTED_LABELS:
        tc_rows, tc_meta = db.cypher_query(top_connected_query(label), {})
        top_connected[label.lower() + 's'] = [
            {
                'slug': r['slug'],
                'name': r['name'],
                'connections_count': int(r['connections_count']),
            }
            for r in _rows_to_dicts(tc_rows, tc_meta)
        ]

    return top_connected


def _compute_global_stats_most_liked() -> list[dict[str, Any]]:
    liked_rows, liked_meta = db.cypher_query(MOST_LIKED_QUERY, {})
    most_liked = [
        {
            'slug': r['slug'],
            'name': r['name'],
            'type': _entity_type_from_labels(r['lbls']),
            'count': int(r['count']),
        }
        for r in _rows_to_dicts(liked_rows, liked_meta)
    ]

    return most_liked


def _compute_global_stats_most_commented() -> list[dict[str, Any]]:
    commented_rows, commented_meta = db.cypher_query(MOST_COMMENTED_QUERY, {})
    most_commented = [
        {
            'slug': r['slug'],
            'name': r['name'],
            'type': _entity_type_from_labels(r['lbls']),
            'count': int(r['count']),
        }
        for r in _rows_to_dicts(commented_rows, commented_meta)
    ]

    return most_commented

def _compute_global_stats() -> dict[str, Any]:
    '''
    Run all Cypher queries and assemble the GlobalStats payload.

    Separated from global_stats() so it is testable without cache interaction.
    '''
    counts = _compute_global_stats_counts()
    characters_by_race = _compute_global_stats_character_by_race()
    characters_by_gender = _compute_global_stats_characters_by_gender()
    characters_by_is_alive = _compute_global_stats_character_by_is_alive()
    events_by_timeline = _compute_global_stats_events_by_timeline()
    locations_by_type = _compute_global_stats_locations_by_type()
    items_by_type = _compute_global_stats_items_by_type()
    top_connected = _compute_global_stats_top_connected()
    most_liked = _compute_global_stats_most_liked()
    most_commented = _compute_global_stats_most_commented()

    return {
        'counts': counts,
        'characters_by_race': characters_by_race,
        'characters_by_gender': characters_by_gender,
        'is_alive_stats': characters_by_is_alive,
        'events_by_timeline': events_by_timeline,
        'locations_by_type': locations_by_type,
        'items_by_type': items_by_type,
        'top_connected': top_connected,
        'most_liked': most_liked,
        'most_commented': most_commented,
    }


# Public API

def global_stats() -> dict[str, Any]:
    '''
    Return aggregated statistics for the entire wiki graph.

    Results are cached for settings.ANALYTICS_GLOBAL_CACHE_TTL seconds
    Call invalidate_global_stats_cache() to clear the cache when the graph changes
    (e.g. after bulk import).
    '''
    cached = cache.get(GLOBAL_STATS_CACHE_KEY)
    if cached is not None:
        return cached

    result = _compute_global_stats()
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

