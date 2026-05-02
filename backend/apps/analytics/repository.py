'''
Repository layer for the analytics app.
    Responsibility: translate between Cypher/Neo4j and Python data structures.
    No business logic, no caching, no HTTP concerns.

TypedDicts are used for return types - work seamlessly with DRF's Response,
and add zero runtime overhead.
'''

from typing import Any, TypedDict

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

# Return-type definitions

class Counts(TypedDict):
    total: int
    characters: int
    races: int
    locations: int
    events: int
    organizations: int
    timelines: int
    items: int
    languages: int
    scripts: int


class CharacterRaceCount(TypedDict):
    slug: str
    name: str
    count: int


class CharacterGenderCount(TypedDict):
    gender: str
    count: int


class CharacterIsAliveStats(TypedDict):
    alive: int
    deceased: int


class TimelineEventCount(TypedDict):
    timeline_slug: str
    name: str
    count: int


class TypeCount(TypedDict):
    type: str
    count: int


class TopConnectedItem(TypedDict):
    slug: str
    name: str
    connections_count: int


class PageEngagement(TypedDict):
    slug: str
    name: str
    type: str
    count: int


# Internal utility

# Internal helpers

def _rows_to_dicts(rows: list, meta: list[str]) -> list[dict[str, Any]]:
    return [dict(zip(meta, row, strict=True)) for row in rows]


def _entity_type_from_labels(labels: list[str]) -> str:
    for label in labels:
        if label != 'Page':
            return label.lower()

    return 'unknown'


class GlobalStatsRepository:

    def get_counts(self) -> Counts:
        count_rows, count_meta = db.cypher_query(COUNTS_QUERY, {})
        if not count_rows:
            return Counts(
                total=0,
                characters=0,
                races=0,
                locations=0,
                events=0,
                organizations=0,
                timelines=0,
                items=0,
                languages=0,
                scripts=0,
            )

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
        return Counts(**counts)

    def get_characters_by_race(self) -> list[CharacterRaceCount]:
        race_rows, race_meta = db.cypher_query(CHARACTERS_BY_RACE_QUERY, {})
        characters_by_race = [
            CharacterRaceCount(
                slug=r['slug'],
                name=r['name'],
                count=int(r['count']),
            )
            for r in _rows_to_dicts(race_rows, race_meta)
        ]

        return characters_by_race

    def get_characters_by_gender(self) -> list[CharacterGenderCount]:
        gender_rows, gender_meta = db.cypher_query(CHARACTERS_BY_GENDER_QUERY, {})
        characters_by_gender = [
            CharacterGenderCount(
                gender=r['gender'],
                count=int(r['count']),
            )
            for r in _rows_to_dicts(gender_rows, gender_meta)
        ]

        return characters_by_gender

    def get_characters_by_is_alive(self) -> CharacterIsAliveStats:
        alive_rows, alive_meta = db.cypher_query(CHARACTERS_BY_IS_ALIVE_COUNT_QUERY, {})
        alive_row = dict(
            zip(alive_meta, alive_rows[0], strict=True)
        ) if alive_rows else {}
        is_alive_stats = CharacterIsAliveStats(
            alive=int(alive_row.get('alive', 0)),
            deceased=int(alive_row.get('deceased', 0)),
        )

        return is_alive_stats

    def get_events_by_timeline(self) -> list[TimelineEventCount]:
        tl_rows, tl_meta = db.cypher_query(EVENTS_BY_TIMELINE_QUERY, {})
        events_by_timeline = [
            TimelineEventCount(
                timeline_slug=r['timeline_slug'],
                name=r['name'],
                count=int(r['count']),
            )
            for r in _rows_to_dicts(tl_rows, tl_meta)
        ]

        return events_by_timeline

    def get_locations_by_type(self) -> list[TypeCount]:
        loc_rows, loc_meta = db.cypher_query(LOCATIONS_BY_TYPE_QUERY, {})
        locations_by_type = [
            TypeCount(
                type=r['type'],
                count=int(r['count']),
            )
            for r in _rows_to_dicts(loc_rows, loc_meta)
        ]

        return locations_by_type

    def get_items_by_type(self) -> list[TypeCount]:
        item_rows, item_meta = db.cypher_query(ITEMS_BY_TYPE_QUERY, {})
        items_by_type = [
            TypeCount(
                type=r['type'],
                count=int(r['count']),
            )
            for r in _rows_to_dicts(item_rows, item_meta)
        ]

        return items_by_type

    def get_top_connected(self) -> dict[str, list[TopConnectedItem]]:
        top_connected: dict[str, list[TopConnectedItem]] = {}
        for label in TOP_CONNECTED_LABELS:
            tc_rows, tc_meta = db.cypher_query(top_connected_query(label), {})
            top_connected[label.lower() + 's'] = [
                TopConnectedItem(
                    slug=r['slug'],
                    name=r['name'],
                    connections_count=int(r['connections_count']),
                )
                for r in _rows_to_dicts(tc_rows, tc_meta)
            ]

        return top_connected

    def get_most_liked(self) -> list[PageEngagement]:
        liked_rows, liked_meta = db.cypher_query(MOST_LIKED_QUERY, {})
        most_liked = [
            PageEngagement(
                slug=r['slug'],
                name=r['name'],
                type=_entity_type_from_labels(r['lbls']),
                count=int(r['count']),
            )
            for r in _rows_to_dicts(liked_rows, liked_meta)
        ]

        return most_liked

    def get_most_commented(self) -> list[PageEngagement]:
        commented_rows, commented_meta = db.cypher_query(MOST_COMMENTED_QUERY, {})
        most_commented = [
            PageEngagement(
                slug=r['slug'],
                name=r['name'],
                type=_entity_type_from_labels(r['lbls']),
                count=int(r['count']),
            )
            for r in _rows_to_dicts(commented_rows, commented_meta)
        ]

        return most_commented
