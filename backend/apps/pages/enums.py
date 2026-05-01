'''
Domain enumerations for the pages app.

All enums inherit from StrEnum so they behave as plain strings in JSON
serialization, Cypher parameters, and Django choices - so no .value.
'''
from enum import StrEnum


class EntityType(StrEnum):
    CHARACTER = 'character'
    RACE = 'race'
    LOCATION = 'location'
    EVENT = 'event'
    ORGANIZATION = 'organization'
    TIMELINE = 'timeline'
    ITEM = 'item'
    LANGUAGE = 'language'
    SCRIPT = 'script'


class Gender(StrEnum):
    MALE = 'male'
    FEMALE = 'female'
    UNKNOWN = 'unknown'


class RelType(StrEnum):
    '''All relationship types that may appear in the wiki graph'''

    # Character
    OF_RACE = 'OF_RACE'
    BORN_IN = 'BORN_IN'
    DIED_IN = 'DIED_IN'
    DWELLED_IN = 'DWELLED_IN'
    SPEAKS = 'SPEAKS'
    CHILD_OF = 'CHILD_OF'
    MARRIED_TO = 'MARRIED_TO'
    SIBLING_OF = 'SIBLING_OF'
    PARTICIPATED_IN = 'PARTICIPATED_IN'
    LIVED_DURING = 'LIVED_DURING'
    RULED = 'RULED'
    MEMBER_OF = 'MEMBER_OF'
    WIELDS = 'WIELDS'
    OWNS = 'OWNS'
    BORE = 'BORE'
    CRAFTED = 'CRAFTED'

    # Race
    SUBRACE_OF = 'SUBRACE_OF'
    INHABITS = 'INHABITS'

    # Location
    REGION_OF = 'REGION_OF'

    # Event
    TOOK_PLACE_IN = 'TOOK_PLACE_IN'
    PART_OF = 'PART_OF'
    OCCURRED_DURING = 'OCCURRED_DURING'

    # Organization
    BASED_IN = 'BASED_IN'

    # Language
    SPOKEN_BY = 'SPOKEN_BY'
    SPOKEN_IN = 'SPOKEN_IN'
    WRITTEN_IN = 'WRITTEN_IN'

class SocRelTypes(StrEnum):
    LIKED = 'LIKED'
    WROTE = 'WROTE'
    ON = 'ON'
    IN_CATEGORY = 'IN_CATEGORY'
    HAS_ARTICLE = 'HAS_ARTICLE'
    SUBCATEGORY_OF = 'SUBCATEGORY_OF'
