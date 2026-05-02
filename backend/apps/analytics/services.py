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

from .repository import GlobalStatsRepository

GLOBAL_STATS_CACHE_KEY = 'analytics:global_stats'


def _assemble(repo: GlobalStatsRepository) -> dict[str, Any]:
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


# Public API

def global_stats(
        repo: GlobalStatsRepository | None = None
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

    result = _assemble(repo or GlobalStatsRepository())
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

