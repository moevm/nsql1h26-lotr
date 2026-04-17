from dataclasses import dataclass
from typing import Any, Protocol


class _HasCypherWhere(Protocol):
    '''Filter protocol - only for type hints, not for inheritance'''
    def to_cypher_where(self) -> tuple[str, dict[str, Any]]:
        raise NotImplementedError


@dataclass
class CharacterFilter:
    '''
    Filters for character catalog.
    Each field is a separate input on the frontend.
    Text fields: case-insensitive substring search.
    '''

    name: str | None = None
    titles: str | None = None
    gender: str | None = None
    is_alive: bool | None = None  # None -> all
    birth_date: str | None = None
    death_date: str | None = None
    hair: str | None = None
    eyes: str | None = None
    height: str | None = None
    weapon: str | None = None
    clothing: str | None = None
    notable_for: str | None = None

    # JOIN-filters
    race_slug: str | None = None
    born_in_slug: str | None = None

    def to_cypher_where(self) -> tuple[str, dict[str, Any]]:
        conditions: list[str] = []
        params: dict[str, Any] = {}

        if self.name:
            conditions.append(
                'ANY(n IN c.names WHERE toLower(n) CONTAINS toLower($name))'
            )
            params['name'] = self.name

        if self.titles:
            conditions.append(
                'ANY(t in c.titles WHERE toLower(t) CONTAINS toLower($titles))'
            )
            params['titles'] = self.titles

        if self.gender:
            conditions.append(
                'toLower(c.gender) = toLower($gender)'
            )
            params['gender'] = self.gender

        if self.is_alive is True:
            conditions.append(
                'c.deathDate IS NULL'
            )
        elif self.is_alive is False:
            conditions.append(
                'c.deathDate IS NOT NULL'
            )

        for field, param_key, cypher_prop in [
            (self.birth_date, 'birth_date', 'c.birthDate'),
            (self.death_date, 'death_date', 'c.deathDate'),
            (self.hair, 'hair', 'c.hair'),
            (self.eyes, 'eyes', 'c.eyes'),
            (self.height, 'height', 'c.height'),
            (self.weapon, 'weapon', 'c.weapon'),
            (self.clothing, 'clothing', 'c.clothing'),
            (self.notable_for, 'notable_for', 'c.notableFor'),
        ]:
            if field:
                conditions.append(
                    f'toLower({cypher_prop}) CONTAINS toLower(${param_key})'
                )
                params[param_key] = field

        # JOIN-filters: OPTIONAL MATCH in main query
        # NULL = $param is always FALSE, so nodes w/o the relation will be
        # filtered correctly
        if self.race_slug:
            conditions.append('race.slug = $race_slug')
            params['race_slug'] = self.race_slug

        if self.born_in_slug:
            conditions.append('born_loc.slug = $born_in_slug')
            params['born_in_slug'] = self.born_in_slug

        where = ('WHERE ' + ' AND '.join(conditions)) if conditions else ''

        print(f"[DEBUG] is_alive = {self.is_alive}")
        print(f"[DEBUG] conditions = {conditions}")

        return where, params


@dataclass
class RaceFilter:
    name: str | None = None
    lifespan: str | None = None
    avg_height: str | None = None
    hair: str | None = None
    eyes: str | None = None
    skin: str | None = None
    weaponry: str | None = None
    clothing: str | None = None
    distinctions: str | None = None

    def to_cypher_where(self) -> tuple[str, dict[str, Any]]:
        conditions: list[str] = []
        params: dict[str, Any] = {}

        if self.name:
            conditions.append(
                'ANY(n IN r.names WHERE toLower(n) CONTAINS toLower($name))'
            )
            params['name'] = self.name

        for field, param_key, cypher_prop in [
            (self.lifespan, 'lifespan', 'r.lifespan'),
            (self.avg_height, 'avg_height', 'r.avgHeight'),
            (self.hair, 'hair', 'r.hair'),
            (self.eyes, 'eyes', 'r.eyes'),
            (self.skin, 'skin', 'r.skin'),
            (self.weaponry, 'weaponry', 'r.weaponry'),
            (self.clothing, 'clothing', 'r.clothing'),
            (self.distinctions, 'distinctions', 'r.distinctions'),
        ]:
            if field:
                conditions.append(
                    f'toLower({cypher_prop}) CONTAINS toLower(${param_key})'
                )
                params[param_key] = field

        where = ('WHERE ' + ' AND '.join(conditions)) if conditions else ''

        return where, params


@dataclass
class LocationFilter:
    name: str | None = None
    entity_type: str | None = None  # Cypher: l.type
    population: str | None = None
    creation_date: str | None = None
    destruction_date: str | None = None
    notable_for: str | None = None
    is_destroyed: bool | None = None  # destuctionDate IS NULL / IS NOT NULL

    def to_cypher_where(self) -> tuple[str, dict[str, Any]]:
        conditions: list[str] = []
        params: dict[str, Any] = {}

        if self.name:
            conditions.append(
                'ANY(n in l.names WHERE toLower(n) CONTAINS toLower($name))'
            )
            params['name'] = self.name

        if self.is_destroyed is True:
            conditions.append(
                'l.destructionDate IS NOT NULL'
            )
        elif self.is_destroyed is False:
            conditions.append(
                'l.destructionDate IS NULL'
            )

        for field, param_key, cypher_prop in [
            (self.entity_type, 'entity_type', 'l.type'),
            (self.population, 'population', 'l.population'),
            (self.creation_date, 'creation_date', 'l.creationDate'),
            (self.destruction_date, 'destruction_date', 'l.destructionDate'),
            (self.notable_for, 'notable_for', 'l.notableFor'),
        ]:
            if field:
                conditions.append(
                    f'toLower({cypher_prop}) CONTAINS toLower(${param_key})'
                )
                params[param_key] = field

        where = ('WHERE ' + ' AND '.join(conditions)) if conditions else ''

        return where, params


@dataclass
class EventFilter:
    name: str | None = None
    entity_type: str | None = None  # Cypher: l.type
    start_date: str | None = None
    end_date: str | None = None
    casualties: str | None = None
    notable_for: str | None = None

    def to_cypher_where(self) -> tuple[str, dict[str, Any]]:
        conditions: list[str] = []
        params: dict[str, Any] = {}

        if self.name:
            conditions.append(
                'ANY(n in e.names WHERE toLower(n) CONTAINS toLower($name))'
            )
            params['name'] = self.name

        for field, param_key, cypher_prop in [
            (self.entity_type, 'entity_type', 'e.type'),
            (self.start_date, 'start_date', 'e.startDate'),
            (self.end_date, 'end_date', 'e.endDate'),
            (self.casualties, 'casualties', 'e.casualties'),
            (self.notable_for, 'notable_for', 'e.notableFor'),
        ]:
            if field:
                conditions.append(
                    f'toLower({cypher_prop}) CONTAINS toLower(${param_key})'
                )
                params[param_key] = field

        where = ('WHERE ' + ' AND '.join(conditions)) if conditions else ''

        return where, params


@dataclass
class OrganizationFilter:
    name: str | None = None
    entity_type: str | None = None  # Cypher: l.type
    founded_date: str | None = None
    dissolved_date: str | None = None
    clothing: str | None = None
    weaponry: str | None = None
    purpose: str | None = None
    notable_for: str | None = None
    is_dissolved: bool | None = None

    def to_cypher_where(self) -> tuple[str, dict[str, Any]]:
        conditions: list[str] = []
        params: dict[str, Any] = {}

        if self.name:
            conditions.append(
                'ANY(n in o.names WHERE toLower(n) CONTAINS toLower($name))'
            )
            params['name'] = self.name

        if self.is_dissolved is True:
            conditions.append(
                'o.dissolvedDate IS NOT NULL'
            )
        elif self.is_dissolved is False:
            conditions.append(
                'o.dissolvedDate IS NULL'
            )

        for field, param_key, cypher_prop in [
            (self.entity_type, 'entity_type', 'o.type'),
            (self.founded_date, 'founded_date', 'o.foundedDate'),
            (self.dissolved_date, 'dissolved_date', 'o.dissolvedDate'),
            (self.clothing, 'clothing', 'o.clothing'),
            (self.weaponry, 'weaponry', 'o.weaponry'),
            (self.purpose, 'purpose', 'o.purpose'),
            (self.notable_for, 'notable_for', 'o.notableFor'),
        ]:
            if field:
                conditions.append(
                    f'toLower({cypher_prop}) CONTAINS toLower(${param_key})'
                )
                params[param_key] = field

        where = ('WHERE ' + ' AND '.join(conditions)) if conditions else ''

        return where, params


@dataclass
class TimelineFilter:
    name: str | None = None
    abbreviation: str | None = None
    start_date: str | None = None
    end_date: str | None = None

    def to_cypher_where(self) -> tuple[str, dict[str, Any]]:
        conditions: list[str] = []
        params: dict[str, Any] = {}

        if self.name:
            conditions.append(
                'ANY(n in t.names WHERE toLower(n) CONTAINS toLower($name))'
            )
            params['name'] = self.name

        for field, param_key, cypher_prop in [
            (self.abbreviation, 'abbreviation', 't.abbreviation'),
            (self.start_date, 'start_date', 't.startDate'),
            (self.end_date, 'end_date', 't.endDate'),
        ]:
            if field:
                conditions.append(
                    f'toLower({cypher_prop}) CONTAINS toLower(${param_key})'
                )
                params[param_key] = field

        where = ('WHERE ' + ' AND '.join(conditions)) if conditions else ''

        return where, params


@dataclass
class ItemFilter:
    name: str | None = None
    entity_type: str | None = None  # Cypher: l.type
    material: str | None = None
    notable_for: str | None = None

    def to_cypher_where(self) -> tuple[str, dict[str, Any]]:
        conditions: list[str] = []
        params: dict[str, Any] = {}

        if self.name:
            conditions.append(
                'ANY(n in i.names WHERE toLower(n) CONTAINS toLower($name))'
            )
            params['name'] = self.name

        for field, param_key, cypher_prop in [
            (self.entity_type, 'entity_type', 'i.type'),
            (self.material, 'material', 'i.material'),
            (self.notable_for, 'notable_for', 'i.notableFor'),
        ]:
            if field:
                conditions.append(
                    f'toLower({cypher_prop}) CONTAINS toLower(${param_key})'
                )
                params[param_key] = field

        where = ('WHERE ' + ' AND '.join(conditions)) if conditions else ''

        return where, params


@dataclass
class LanguageFilter:
    name: str | None = None
    family: str | None = None

    def to_cypher_where(self) -> tuple[str, dict[str, Any]]:
        conditions: list[str] = []
        params: dict[str, Any] = {}

        if self.name:
            conditions.append(
                'ANY(n in lang.names WHERE toLower(n) CONTAINS toLower($name))'
            )
            params['name'] = self.name

        for field, param_key, cypher_prop in [
            (self.family, 'family', 'lang.family'),
        ]:
            if field:
                conditions.append(
                    f'toLower({cypher_prop}) CONTAINS toLower(${param_key})'
                )
                params[param_key] = field

        where = ('WHERE ' + ' AND '.join(conditions)) if conditions else ''

        return where, params


@dataclass
class ScriptFilter:
    name: str | None = None

    def to_cypher_where(self) -> tuple[str, dict[str, Any]]:
        conditions: list[str] = []
        params: dict[str, Any] = {}

        if self.name:
            conditions.append(
                'ANY(n in s.names WHERE toLower(n) CONTAINS toLower($name))'
            )
            params['name'] = self.name

        where = ('WHERE ' + ' AND '.join(conditions)) if conditions else ''

        return where, params
