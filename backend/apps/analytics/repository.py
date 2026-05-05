'''
Repository layer for the analytics app.
    Responsibility: translate between Cypher/Neo4j and Python data structures.
    No business logic, no caching, no HTTP concerns.

TypedDicts are used for return types - work seamlessly with DRF's Response,
and add zero runtime overhead.

Protocol vs ABC:
    We use typing.Protocol rather than ABC.
    Fake implementations in tests do not need to inherit from anything - they only
    need matching method signatures.
    This avoids inheritance coupling and is idiomatic in modern Python.

TypedDict vs dataclass:
    We use TypedDict for objects that are immediately passed to Response.
    Dataclasses are internal objects to be filtered and enriched.
    Don't know if that is the best practice, might need to look at it
    again after some time.
'''

from dataclasses import dataclass, field
from typing import Protocol, TypedDict, runtime_checkable

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
    NEIGHBORS_EDGES_QUERY,
    NEIGHBORS_NODES_QUERY,
    NEIGHBORS_ROOT_QUERY,
    TOP_CONNECTED_LABELS,
    top_connected_query,
)
from .utils import entity_type_from_labels, rows_to_dicts

# Value-object types

# Global stats

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

# Neighbors
@dataclass(frozen=True)
class PageRow:
    '''Minimal representation of a :Page node returned from the DB.'''

    slug: str
    names: list[str]
    node_labels: list[str]
    image_url: str | None


@dataclass(frozen=True)
class EdgeRow:
    '''A directed lore edge between two :Page nodes.'''

    from_slug: str
    to_slug: str
    rel_type: str
    rel_properties: dict = field(default_factory=dict)


# Repository interfaces (Protocols)

@runtime_checkable
class GlobalStatsRepositoryProtocol(Protocol):
    '''Interface for the global statistics repository.'''

    def get_counts(self) -> Counts:
        '''Return total and per‑type page counts.'''
        ...

    def get_characters_by_race(self) -> list[CharacterRaceCount]:
        '''
        Return character count grouped by race (only characters with an OF_RACE edge).
        '''
        ...

    def get_characters_by_gender(self) -> list[CharacterGenderCount]:
        '''Return character count grouped by gender.'''
        ...

    def get_characters_by_is_alive(self) -> CharacterIsAliveStats:
        '''Return alive/deceased counts based on presence/absence of death date.'''
        ...

    def get_events_by_timeline(self) -> list[TimelineEventCount]:
        '''Return event count grouped by timeline.'''
        ...

    def get_locations_by_type(self) -> list[TypeCount]:
        '''Return location count grouped by location type.'''
        ...

    def get_items_by_type(self) -> list[TypeCount]:
        '''Return item count grouped by item type.'''
        ...

    def get_top_connected(self) -> dict[str, list[TopConnectedItem]]:
        '''
        Return the most connected nodes for each entity type.

        Only lore relationships are counted (social/UI relations are excluded).
        The key is the pluralised entity type (e.g. 'characters', 'locations').
        '''
        ...

    def get_most_liked(self) -> list[PageEngagement]:
        '''Return pages with the most likes.'''
        ...

    def get_most_commented(self) -> list[PageEngagement]:
        '''Return pages with the most comments.'''
        ...


@runtime_checkable
class NeighborsRepositoryProtocol(Protocol):
    '''Interface for the neighbors repository'''

    def get_root(self, slug: str) -> PageRow | None:
        '''
        Return display data for the root page, or None if not found.

        This is intentionally a separate call from get_neighbors so the
        service can raise NotFound before the heavier traversal query.
        '''
        ...

    def get_neighbors(
            self,
            slug: str,
            depth: int,
            node_labels: list[str] | None,
            rel_types: list[str] | None,
            limit: int,
    ) -> list[PageRow]:
        '''
        Return :Page nodes reachable from slug within depth.

        node_labels - if given, only paths where ALL non-root nodes carry
            one of these labels are considered (i.e. both intermediate and endpoint
            nodes are filtered). None means all node types are traversable.
        '''
        ...

    def get_induced_edges(
            self,
            slugs: list[str],
            rel_types: list[str] | None,
    ) -> list[EdgeRow]:
        '''
        Return all directed lore edges whose both endpoints are in slugs.

        rel_types - if given, only edges of those types are returned.
            None means all relationship types.
        '''
        ...



# Neo4j repository implementations

def _fetch_page(slug: str) -> PageRow | None:
    '''
    Fetch a single :Page node by slug and return it as a PageRow.
    '''
    result_rows, meta = db.cypher_query(NEIGHBORS_ROOT_QUERY, {'slug': slug})
    if not result_rows:
        return None

    row = rows_to_dicts(result_rows, meta)[0]
    return PageRow(
        slug=row['slug'],
        names=row['names'] or [],
        node_labels=row['node_labels'] or [],
        image_url=row.get('image_url'),
    )


class Neo4jGlobalStatsRepository:
    '''Concrete repository for global stats backed by Neo4j.'''

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
            for r in rows_to_dicts(race_rows, race_meta)
        ]

        return characters_by_race

    def get_characters_by_gender(self) -> list[CharacterGenderCount]:
        gender_rows, gender_meta = db.cypher_query(CHARACTERS_BY_GENDER_QUERY, {})
        characters_by_gender = [
            CharacterGenderCount(
                gender=r['gender'],
                count=int(r['count']),
            )
            for r in rows_to_dicts(gender_rows, gender_meta)
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
            for r in rows_to_dicts(tl_rows, tl_meta)
        ]

        return events_by_timeline

    def get_locations_by_type(self) -> list[TypeCount]:
        loc_rows, loc_meta = db.cypher_query(LOCATIONS_BY_TYPE_QUERY, {})
        locations_by_type = [
            TypeCount(
                type=r['type'],
                count=int(r['count']),
            )
            for r in rows_to_dicts(loc_rows, loc_meta)
        ]

        return locations_by_type

    def get_items_by_type(self) -> list[TypeCount]:
        item_rows, item_meta = db.cypher_query(ITEMS_BY_TYPE_QUERY, {})
        items_by_type = [
            TypeCount(
                type=r['type'],
                count=int(r['count']),
            )
            for r in rows_to_dicts(item_rows, item_meta)
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
                for r in rows_to_dicts(tc_rows, tc_meta)
            ]

        return top_connected

    def get_most_liked(self) -> list[PageEngagement]:
        liked_rows, liked_meta = db.cypher_query(MOST_LIKED_QUERY, {})
        most_liked = [
            PageEngagement(
                slug=r['slug'],
                name=r['name'],
                type=entity_type_from_labels(r['lbls']),
                count=int(r['count']),
            )
            for r in rows_to_dicts(liked_rows, liked_meta)
        ]

        return most_liked

    def get_most_commented(self) -> list[PageEngagement]:
        commented_rows, commented_meta = db.cypher_query(MOST_COMMENTED_QUERY, {})
        most_commented = [
            PageEngagement(
                slug=r['slug'],
                name=r['name'],
                type=entity_type_from_labels(r['lbls']),
                count=int(r['count']),
            )
            for r in rows_to_dicts(commented_rows, commented_meta)
        ]

        return most_commented


# TODO: remove
class Neo4jNeighborsRepository:
    '''Concrete neighbors repository backed by Neo4j.'''
    def get_root(self, slug: str) -> PageRow | None:
        return _fetch_page(slug)

    def get_neighbors(
        self,
        slug: str,
        depth: int,
        node_labels: list[str] | None,
        rel_types: list[str] | None,
        limit: int,
    ) -> list[PageRow]:
        result_rows, meta = db.cypher_query(
            NEIGHBORS_NODES_QUERY.format(depth=depth),
            {
                'slug': slug,
                # 'depth': depth,
                'node_labels': node_labels,
                'rel_types': rel_types,
                'limit': limit,
            },
        )

        return [
            PageRow(
                slug=r['slug'],
                names=r['names'] or [],
                node_labels=r['node_labels'] or [],
                image_url=r.get('image_url'),
            )
            for r in rows_to_dicts(result_rows, meta)
        ]

    def get_induced_edges(
        self,
        slugs: list[str],
        rel_types: list[str] | None,
    ) -> list[EdgeRow]:
        result_rows, meta = db.cypher_query(
            NEIGHBORS_EDGES_QUERY,
            {
                'slugs': slugs,
                'rel_types': rel_types,
            },
        )

        return [
            EdgeRow(
                from_slug=r['from_slug'],
                to_slug=r['to_slug'],
                rel_type=r['rel_type'],
                rel_properties=r['rel_properties'] or {},
            )
            for r in rows_to_dicts(result_rows, meta)
        ]
