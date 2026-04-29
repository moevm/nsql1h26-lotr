'''
Filter dataclasses for catalog list endpoints.

Multi-value syntax
Any string filter accepts comma-separated values, interpreted as OR.

JOIN filters

Notes on relationship coverage
- Character <-> Location : BORN_IN | DIED_IN | DWELLED_IN
- Character <-> Item : OWNS | CRAFTED | BORE | WIELDS
'''

from dataclasses import dataclass
from typing import Any, Protocol

# Maximum number of OR values per multi-value filter param.
# Prevents accidental abuse / oversized queries.
_MAX_MULTI: int = 20


class CypherWhereFilter(Protocol):
    '''Filter protocol - only for type hints, not for inheritance'''
    def to_cypher_where(self) -> tuple[str, dict[str, Any]]:
        raise NotImplementedError


# Low-level helper functions


def _parse_multi(value: str | None) -> list[str]:
    '''
    Parse comma-separated query parameter into a list of stripped value

    Empty string or None returns []
    Result is capped at _MAX_MULTI to protect query size
    '''
    if not value:
        return []

    patrs = [v.strip() for v in value.split(',') if v.strip()]

    return patrs[:_MAX_MULTI]


def _add(
        conditons: list[str],
        params: dict[str, Any],
        result: tuple[str | None, dict[str, Any]],
) -> None:
    '''
    Append a (clause, params) pair to the accumulator when clause is not None
    '''
    clause, p = result

    if clause:
        conditons.append(clause)
        params.update(p)


def _text_multi(
    alias: str,
    prop: str,
    param: str,
    values: list[str],
) -> tuple[str | None, dict[str, Any]]:
    '''
    Case-insensitive substring match, OR across values.

    Generates:
        ANY(v IN $param WHERE toLower(alias.prop) CONTAINS toLower(v))
    '''
    if not values:
        return None, {}

    return (
        f'ANY(v IN ${param} WHERE toLower({alias}.{prop}) CONTAINS toLower(v))',
        {param: values},
    )


def _list_text_multi(
    alias: str,
    prop: str,
    param: str,
    values: list[str],
) -> tuple[str | None, dict[str, Any]]:
    '''
    Array property: any element matches any of the given values
    (case-insensitive substring), OR across values.

    Generates:
        ANY(
            v IN $param
            WHERE ANY(
                n IN alias.prop
                WHERE toLower(n)
                CONTAINS toLower(v)
            )
        )
    '''
    if not values:
        return None, {}

    return (
        f'ANY(v IN ${param} WHERE '
        f'ANY(n IN {alias}.{prop} WHERE toLower(n) CONTAINS toLower(v)))',
        {param: values},
    )


def _exact_multi(
    alias: str,
    prop: str,
    param: str,
    values: list[str],
) -> tuple[str | None, dict[str, Any]]:
    '''
    Case-insensitive exact match, OR across values.
    Used for enum fields like gender.

    Generates:
        ANY(v IN $param WHERE toLower(alias.prop) = toLower(v))
    '''
    if not values:
        return None, {}

    return (
        f'ANY(v IN ${param} WHERE toLower({alias}.{prop}) = toLower(v))',
        {param: values},
    )


def _exists_out(
    outer_var: str,
    rel_types: str,
    target_label: str,
    param: str,
    slugs: list[str],
) -> tuple[str | None, dict[str, Any]]:
    '''
    EXISTS filter for an outgoing relationship.

    Generates:
        EXISTS {
            MATCH (outer_var)-[:REL_TYPES]->(xn:Label) WHERE xn.slug IN $param
        }

    `xn` is the inner-scope variable; it never shadows the outer scope
    because it is a fresh name not used in the enclosing query.
    '''
    if not slugs:
        return None, {}

    clause = (
        f'EXISTS {{ MATCH ({outer_var})-[:{rel_types}]->(xn:{target_label}) '
        f'WHERE xn.slug IN ${param} }}'
    )
    return clause, {param: slugs}


def _exists_in(
    outer_var: str,
    source_label: str,
    rel_types: str,
    param: str,
    slugs: list[str],
) -> tuple[str | None, dict[str, Any]]:
    '''
    EXISTS filter for an incoming relationship.

    Generates:
        EXISTS {
            MATCH (xn:Label)-[:REL_TYPES]->(outer_var) WHERE xn.slug IN $param
        }
    '''
    if not slugs:
        return None, {}

    clause = (
        f'EXISTS {{ MATCH (xn:{source_label})-[:{rel_types}]->({outer_var}) '
        f'WHERE xn.slug IN ${param} }}'
    )
    return clause, {param: slugs}


def _build_where(conditions: list[str]) -> str:
    return ('WHERE ' + ' AND '.join(conditions)) if conditions else ''


# Filter dataclasses


@dataclass
class CharacterFilter:
    '''
    Filters for character catalog GET /characters/.

    All string fields accept comma-separated values (OR).
    Boolean fields (is_alive) remain single-value.
    JOIN filters:
        race - slug(s) of the character's race
            (OF_RACE)
        organization - slug(s) of an organization the character belongs to
            (MEMBER_OF)
        event - slug(s) of an event the character participated in
            (PARTICIPATED_IN)
        item - slug(s) of an item the character has any relation to
            (OWNS|WIELDS|BORE|CRAFTED)
        location - slug(s) of a location the character is connected to
            (BORN_IN|DIED_IN|DWELLED_IN)
    '''

    name: str | None = None
    titles: str | None = None
    gender: str | None = None
    is_alive: bool | None = None  # None -> no filter
    birth_date: str | None = None
    death_date: str | None = None
    hair: str | None = None
    eyes: str | None = None
    height: str | None = None
    weapon: str | None = None
    clothing: str | None = None
    notable_for: str | None = None

    # JOIN-filters
    race: str | None = None
    organization: str | None = None
    event: str | None = None
    item: str | None = None
    location: str | None = None

    def to_cypher_where(self) -> tuple[str, dict[str, Any]]:
        conditions: list[str] = []
        params: dict[str, Any] = {}

        # Array fields
        _add(
            conditions,
            params,
            _list_text_multi('c', 'names', 'name', _parse_multi(self.name))
        )
        _add(
            conditions,
            params,
            _list_text_multi(
                'c', 'titles', 'titles', _parse_multi(self.titles)
                )
        )

        # Enum fields: exact case-insensitive match
        _add(
            conditions,
            params,
            _exact_multi('c', 'gender', 'gender', _parse_multi(self.gender))
        )

        # Boolean: no multi-value semantics
        if self.is_alive is True:
            conditions.append(
                'c.deathDate IS NULL'
            )
        elif self.is_alive is False:
            conditions.append(
                'c.deathDate IS NOT NULL'
            )

        # Scalar string fields
        for value, param_key, field in [
            (self.birth_date, 'birth_date', 'birthDate'),
            (self.death_date, 'death_date', 'deathDate'),
            (self.hair, 'hair', 'hair'),
            (self.eyes, 'eyes', 'eyes'),
            (self.height, 'height', 'height'),
            (self.weapon, 'weapon', 'weapon'),
            (self.clothing, 'clothing', 'clothing'),
            (self.notable_for, 'notable_for', 'notableFor'),
        ]:
            _add(
                conditions,
                params,
                _text_multi('c', field, param_key, _parse_multi(value))
            )

        # JOIN-filters via EXISTS
        _add(
            conditions,
            params,
            _exists_out(
                'c', 'OF_RACE', 'Race', 'race', _parse_multi(self.race)
            )
        )
        _add(
            conditions,
            params,
            _exists_out(
                'c',
                'MEMBER_OF',
                'Organization',
                'organization',
                _parse_multi(self.organization),
            )
        )
        _add(
            conditions,
            params,
            _exists_out(
                'c',
                'PARTICIPATED_IN',
                'Event',
                'event',
                _parse_multi(self.event),
            )
        )
        _add(
            conditions,
            params,
            _exists_out(
                'c',
                'OWNS|WIELDS|BORE|CRAFTED',
                'Item',
                'item',
                _parse_multi(self.item),
            )
        )
        _add(
            conditions,
            params,
            _exists_out(
                'c',
                'BORN_IN|DIED_IN|DWELLED_IN',
                'Location',
                'location',
                _parse_multi(self.location),
            )
        )

        return _build_where(conditions), params


@dataclass
class RaceFilter:
    '''
    Filters for GET /races/.

    JOIN filters
        location - slug(s) of a location the race inhabits
            (INHABITS)
    '''
    name: str | None = None
    lifespan: str | None = None
    avg_height: str | None = None
    hair: str | None = None
    eyes: str | None = None
    skin: str | None = None
    weaponry: str | None = None
    clothing: str | None = None
    distinctions: str | None = None

    location: str | None = None

    def to_cypher_where(self) -> tuple[str, dict[str, Any]]:
        conditions: list[str] = []
        params: dict[str, Any] = {}

        _add(
            conditions,
            params,
            _list_text_multi('r', 'names', 'name', _parse_multi(self.name))
        )

        for value, param_key, field in [
            (self.lifespan, 'lifespan', 'lifespan'),
            (self.avg_height, 'avg_height', 'avgHeight'),
            (self.hair, 'hair', 'hair'),
            (self.eyes, 'eyes', 'eyes'),
            (self.skin, 'skin', 'skin'),
            (self.weaponry, 'weaponry', 'weaponry'),
            (self.clothing, 'clothing', 'clothing'),
            (self.distinctions, 'distinctions', 'distinctions'),
        ]:
            _add(
                conditions,
                params,
                _text_multi('r', field, param_key, _parse_multi(value))
            )

        _add(
            conditions,
            params,
            _exists_out(
                'r',
                'INHABITS',
                'Location',
                'location',
                _parse_multi(self.location),
            )
        )

        return _build_where(conditions), params


@dataclass
class LocationFilter:
    '''
    Filters for GET /locations/.

    JOIN filters (all incoming - entities connected TO this location)
        character - slug(s) of characters connected via
            BORN_IN|DIED_IN|DWELLED_IN
        event - slug(s) of events that took place here
            (TOOK_PLACE_IN)
        organization - slug(s) of organizations based here
            (BASED_IN)
    '''
    name: str | None = None
    entity_type: str | None = None  # Cypher: l.type
    population: str | None = None
    creation_date: str | None = None
    destruction_date: str | None = None
    notable_for: str | None = None
    is_destroyed: bool | None = None  # destuctionDate IS NULL / IS NOT NULL

    character: str | None = None
    event: str | None = None
    organization: str | None = None

    def to_cypher_where(self) -> tuple[str, dict[str, Any]]:
        conditions: list[str] = []
        params: dict[str, Any] = {}

        _add(
            conditions,
            params,
            _list_text_multi('l', 'names', 'name', _parse_multi(self.name))
        )

        if self.is_destroyed is True:
            conditions.append('l.destructionDate IS NOT NULL')
        elif self.is_destroyed is False:
            conditions.append('l.destructionDate IS NULL')

        for value, param_key, field in [
            (self.entity_type, 'entity_type', 'type'),
            (self.population, 'population', 'population'),
            (self.creation_date, 'creation_date', 'creationDate'),
            (self.destruction_date, 'destruction_date', 'destructionDate'),
            (self.notable_for, 'notable_for', 'notableFor'),
        ]:
            _add(
                conditions,
                params,
                _text_multi('l', field, param_key, _parse_multi(value))
            )

        _add(
            conditions,
            params,
            _exists_in(
                'l',
                'Character',
                'BORN_IN|DIED_IN|DWELLED_IN', 'character',
                _parse_multi(self.character),
            )
        )
        _add(
            conditions,
            params,
            _exists_in(
                'l',
                'Event',
                'TOOK_PLACE_IN', 'event',
                _parse_multi(self.event),
            )
        )
        _add(
            conditions,
            params,
            _exists_in(
                'l',
                'Organization',
                'BASED_IN', 'organization',
                _parse_multi(self.organization),
            )
        )

        return _build_where(conditions), params


@dataclass
class EventFilter:
    '''
    Filters for GET /events/.

    JOIN filters
        character - slug(s) of characters who participated
            (PARTICIPATED_IN, incoming)
        location - slug(s) of locations where the event took place
            (TOOK_PLACE_IN, outgoing)
    '''
    name: str | None = None
    entity_type: str | None = None  # Cypher: e.type
    start_date: str | None = None
    end_date: str | None = None
    casualties: str | None = None
    notable_for: str | None = None

    character: str | None = None
    location: str | None = None

    def to_cypher_where(self) -> tuple[str, dict[str, Any]]:
        conditions: list[str] = []
        params: dict[str, Any] = {}

        _add(
            conditions,
            params,
            _list_text_multi('e', 'names', 'name', _parse_multi(self.name))
        )

        for value, param_key, field in [
            (self.entity_type, 'entity_type', 'type'),
            (self.start_date, 'start_date', 'startDate'),
            (self.end_date, 'end_date', 'endDate'),
            (self.casualties, 'casualties', 'casualties'),
            (self.notable_for, 'notable_for', 'notableFor'),
        ]:
            _add(
                conditions,
                params,
                _text_multi('e', field, param_key, _parse_multi(value))
            )

        _add(
            conditions,
            params,
            _exists_in(
                'e',
                'Character',
                'PARTICIPATED_IN',
                'character',
                _parse_multi(self.character),
            )
        )
        _add(
            conditions,
            params,
            _exists_out(
                'e',
                'TOOK_PLACE_IN',
                'Location',
                'location',
                _parse_multi(self.location),
            )
        )

        return _build_where(conditions), params


@dataclass
class OrganizationFilter:
    '''
    Filters for GET /organizations/.

    JOIN filters:
        character - slug(s) of member characters
            (MEMBER_OF, incoming)
        location - slug(s) of locations the org is based in
            (BASED_IN, outgoing)
    '''
    name: str | None = None
    entity_type: str | None = None  # Cypher: o.type
    founded_date: str | None = None
    dissolved_date: str | None = None
    clothing: str | None = None
    weaponry: str | None = None
    purpose: str | None = None
    notable_for: str | None = None
    is_dissolved: bool | None = None

    character: str | None = None
    location: str | None = None

    def to_cypher_where(self) -> tuple[str, dict[str, Any]]:
        conditions: list[str] = []
        params: dict[str, Any] = {}

        _add(
            conditions,
            params,
            _list_text_multi('o', 'names', 'name', _parse_multi(self.name))
        )

        if self.is_dissolved is True:
            conditions.append('o.dissolvedDate IS NOT NULL')
        elif self.is_dissolved is False:
            conditions.append('o.dissolvedDate IS NULL')

        for value, param_key, field in [
            (self.entity_type, 'entity_type', 'type'),
            (self.founded_date, 'founded_date', 'foundedDate'),
            (self.dissolved_date, 'dissolved_date', 'dissolvedDate'),
            (self.clothing, 'clothing', 'clothing'),
            (self.weaponry, 'weaponry', 'weaponry'),
            (self.purpose, 'purpose', 'purpose'),
            (self.notable_for, 'notable_for', 'notableFor'),
        ]:
            _add(
                conditions,
                params,
                _text_multi('o', field, param_key, _parse_multi(value))
            )

        _add(
            conditions,
            params,
            _exists_in(
                'o',
                'Character',
                'MEMBER_OF',
                'character',
                _parse_multi(self.character),
            )
        )
        _add(
            conditions,
            params,
            _exists_out(
                'o',
                'BASED_IN',
                'Location',
                'location',
                _parse_multi(self.location),
            )
        )

        return _build_where(conditions), params


@dataclass
class TimelineFilter:
    '''Filters for GET /timelines/.'''

    name: str | None = None
    abbreviation: str | None = None
    start_date: str | None = None
    end_date: str | None = None

    def to_cypher_where(self) -> tuple[str, dict[str, Any]]:
        conditions: list[str] = []
        params: dict[str, Any] = {}

        _add(
            conditions,
            params,
            _list_text_multi('t', 'names', 'name', _parse_multi(self.name))
        )

        for value, param_key, field in [
            (self.abbreviation, 'abbreviation', 'abbreviation'),
            (self.start_date, 'start_date', 'startDate'),
            (self.end_date, 'end_date', 'endDate'),
        ]:
            _add(
                conditions,
                params,
                _text_multi('t', field, param_key, _parse_multi(value))
            )

        return _build_where(conditions), params


@dataclass
class ItemFilter:
    '''
    Filters for GET /items/.

    JOIN filters
        character - slug(s) of characters connected to this item via
            OWNS | WIELDS | BORE | CRAFTED  (all incoming)
    '''

    name: str | None = None
    entity_type: str | None = None  # Cypher: i.type
    material: str | None = None
    notable_for: str | None = None

    character: str | None = None

    def to_cypher_where(self) -> tuple[str, dict[str, Any]]:
        conditions: list[str] = []
        params: dict[str, Any] = {}

        _add(
            conditions,
            params,
            _list_text_multi('i', 'names', 'name', _parse_multi(self.name))
        )

        for value, param_key, field in [
            (self.entity_type, 'entity_type', 'type'),
            (self.material, 'material', 'material'),
            (self.notable_for, 'notable_for', 'notableFor'),
        ]:
            _add(
                conditions,
                params,
                _text_multi('i', field, param_key, _parse_multi(value))
            )

        _add(
            conditions,
            params,
            _exists_in(
                'i',
                'Character',
                'OWNS|WIELDS|BORE|CRAFTED',
                'character',
                _parse_multi(self.character),
            )
        )

        return _build_where(conditions), params


@dataclass
class LanguageFilter:
    '''Filter for GET /languages/.'''

    name: str | None = None
    family: str | None = None

    def to_cypher_where(self) -> tuple[str, dict[str, Any]]:
        conditions: list[str] = []
        params: dict[str, Any] = {}

        _add(
            conditions,
            params,
            _list_text_multi('lang', 'names', 'name', _parse_multi(self.name))
        )

        _add(
            conditions,
            params,
            _text_multi('lang', 'family', 'family', _parse_multi(self.family))
        )

        return _build_where(conditions), params


@dataclass
class ScriptFilter:
    '''Filters for GET /scripts/.'''

    name: str | None = None

    def to_cypher_where(self) -> tuple[str, dict[str, Any]]:
        conditions: list[str] = []
        params: dict[str, Any] = {}

        _add(
            conditions,
            params,
            _list_text_multi('s', 'names', 'name', _parse_multi(self.name))
        )

        return _build_where(conditions), params
