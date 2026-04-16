'''
Neo4j graph models.

All wiki-page entities inherit from PageNode which has `:Page` label.
This gives every entity node a double label, e.g. `:Page:Character`

After any change to this file run:
    neomodel_install_labels apps.pages.models --db 'NEO4J_BOLT_URL'
(in docker in is handled automatically by entrypoint.sh)

RelationshipFrom are not yet written - they should 'arise' naturally when
writing views
'''
from __future__ import annotations

# Pyright is being silly with these imports :(
from neomodel import (
    StructuredRel,  # type: ignore
    StructuredNode,  # type: ignore
    StringProperty,  # type: ignore
    DateTimeProperty,  # type: ignore
    IntegerProperty,  # type: ignore
    ArrayProperty,  # type: ignore
    RelationshipTo,  # type: ignore
    RelationshipFrom,  # type: ignore
    ZeroOrMore,  # type: ignore
    ZeroOrOne,  # type: ignore
)


# Relationship models (edges with properties)

class ChildOfRel(StructuredRel):
    '''(:Character)-[:CHILD_OF]->(:Character) - biological/adopted/foster'''

    # `type` is a reserved word
    # map via db_property so the Neo4j property stays `type` while the python
    # attribute is `rel_type`
    rel_type = StringProperty(db_property='type')


class MarriedToRel(StructuredRel):
    '''(:Character)-[MARRIED_TO]->(:Character)'''

    from_date = StringProperty()
    to_date = StringProperty()


class MemberOfRel(StructuredRel):
    '''(:Character)-[MEMBER_OF]->(:Organization)'''

    role = StringProperty()
    from_date = StringProperty()
    to_date = StringProperty()


class ParticipatedInRel(StructuredRel):
    '''(:Character)-[:PARTICIPATED_IN]->(:Event)'''

    role = StringProperty()


class RuledRel(StructuredRel):
    '''(:Character)-[:RULED]->(:Location | :Race)'''

    from_date = StringProperty()
    to_date = StringProperty()


class LikedRel(StructuredRel):
    '''(:UserRef)-[:LIKED]->(:Page)'''

    created_at = DateTimeProperty(default_now=True)


# Non-Page nodes (not part of the `:Page` hierarchy)

class Article(StructuredNode):
    '''
    Full wiki article text. Stored as separate node so that graph traversal
    (MATCH on `:Page`) does not load multi-KB text blobs.
    Connected via (:Page)-[:HAS_ARTICLE]->(:Article)
    '''

    __label__ = 'Article'

    text = StringProperty()
    image_url = StringProperty()
    created_at = DateTimeProperty(default_now=True)
    updated_at = DateTimeProperty(default_now=True)


class Category(StructuredNode):
    '''Wiki category. Pages link via (:Page)-[:IN_CATEGORY]->(:Category)'''

    __label__ = 'Category'

    slug = StringProperty(unique_index=True, required=True)
    name = StringProperty(required=True)
    created_at = DateTimeProperty(default_now=True)

    subcategories = RelationshipTo(
        'Category',
        'SUBCATEGORY_OF',
        cardinality=ZeroOrMore
    )


class UserRef(StructuredNode):
    '''
    Thin Neo4j proxy for a Django user. Only the SQLite pk is stored here,
    no credentials, no role. Auth happens in Django.
    The graph stores social data (likes, comments).
    '''

    __label__ = 'User'

    django_id = IntegerProperty(unique_index=True, required=True)

    liked = RelationshipTo(
        'PageNode',
        'LIKED',
        cardinality=ZeroOrMore,
        model=LikedRel,
    )
    wrote = RelationshipTo('Comment', 'WROTE', cardinality=ZeroOrMore)


class Comment(StructuredNode):
    '''User comment on a Page, or a reply to another Comment'''

    __label__ = 'Comment'

    text = StringProperty(required=True)
    created_at = DateTimeProperty(default_now=True)
    updated_at = DateTimeProperty(default_now=True)

    on = RelationshipTo('PageNode', 'ON', cardinality=ZeroOrMore)
    reply_to = RelationshipTo('Comment', 'REPLY_TO', cardinality=ZeroOrMore)


# Page hierarchy

class PageNode(StructuredNode):
    '''
    Base node for all wiki pages.
    slug - public identifier.
    names - optional list shared by subtypes.
    '''

    __label__ = 'Page'

    slug = StringProperty(unique_index=True, required=True)
    names = ArrayProperty(StringProperty())

    # Every apge may have an artcile and belong to categories
    article = RelationshipTo('Article', 'HAS_ARTICLE', cardinality=ZeroOrOne)
    categories = RelationshipTo(
        'Category',
        'IN_CATEGORY',
        cardinality=ZeroOrMore,
    )

    # Inbound social edges
    liked_by = RelationshipFrom(
        'UserRef',
        'LIKED',
        cardinality=ZeroOrMore,
        model=LikedRel,
    )
    comments = RelationshipFrom('Comment', 'ON', cardinality=ZeroOrMore)


class Character(PageNode):
    '''A character or a creature of the LotR Universe'''

    __label__ = 'Character'

    gender = StringProperty(
        choices={
            'male': 'Male',
            'female': 'Female',
            'unknown': 'Unknown',
        }
    )
    birth_date = StringProperty()
    death_date = StringProperty()
    hair = StringProperty()
    eyes = StringProperty()
    height = StringProperty()
    weapon = StringProperty()
    clothing = StringProperty()
    notable_for = StringProperty()
    titles = ArrayProperty(StringProperty())

    # relationships
    race = RelationshipTo('Race', 'OF_RACE', cardinality=ZeroOrOne)
    born_in = RelationshipTo('Location', 'BORN_IN', cardinality=ZeroOrOne)
    died_in = RelationshipTo('Location', 'DIED_IN', cardinality=ZeroOrOne)
    dwelled_in = RelationshipTo(
        'Location',
        'DWELLED_IN',
        cardinality=ZeroOrMore,
    )
    speaks = RelationshipTo('Language', 'SPEAKS', cardinality=ZeroOrMore)
    child_of = RelationshipTo(
        'Character',
        'CHILD_OF',
        cardinality=ZeroOrMore,
        model=ChildOfRel,
    )
    married_to = RelationshipTo(
        'Character',
        'MARRIED_TO',
        cardinality=ZeroOrMore,
        model=MarriedToRel,
    )
    sibling_of = RelationshipTo(
        'Character',
        'SIBLING_OF',
        cardinality=ZeroOrMore,
    )
    participated_in = RelationshipTo(
        'Event',
        'PARTICIPATED_IN',
        cardinality=ZeroOrMore,
        model=ParticipatedInRel,
    )
    lived_during = RelationshipTo(
        'Timeline',
        'LIVED_DURING',
        cardinality=ZeroOrMore,
    )
    ruled_location = RelationshipTo(
        'Location',
        'RULED',
        cardinality=ZeroOrMore,
        model=RuledRel,
    )
    ruled_race = RelationshipTo(
        'Race',
        'RULED',
        cardinality=ZeroOrMore,
        model=RuledRel,
    )
    member_of = RelationshipTo(
        'Organization',
        'MEMBER_OF',
        cardinality=ZeroOrMore,
        model=MemberOfRel,
    )
    wields = RelationshipTo('Item', 'WIELDS', cardinality=ZeroOrMore)
    owns = RelationshipTo('Item', 'OWNS', cardinality=ZeroOrMore)
    bore = RelationshipTo('Item', 'BORE', cardinality=ZeroOrMore)
    crafted = RelationshipTo('Item', 'CRAFTED', cardinality=ZeroOrMore)


class Race(PageNode):
    '''A race or people of Middle-earth'''

    __label__ = 'Race'

    lifespan = StringProperty()
    avg_height = StringProperty()
    hair = StringProperty()
    eyes = StringProperty()
    skin = StringProperty()
    weaponry = StringProperty()
    clothing = StringProperty()
    distinctions = StringProperty()

    subrace_of = RelationshipTo('Race', "SUBRACE_OF", cardinality=ZeroOrMore)
    inhabits = RelationshipTo('Location', 'INHABITS', cardinality=ZeroOrMore)


class Location(PageNode):
    '''A geographic place: county, mountain, river, settlements, etc.'''

    __label__ = 'Location'

    # `type` clashes with python built-in. use db_property to keep Neo4j name
    entity_type = StringProperty(db_property='type')
    population = StringProperty()
    creation_date = StringProperty()
    destruction_date = StringProperty()
    notable_for = StringProperty()

    region_of = RelationshipTo('Location', 'REGION_OF', cardinality=ZeroOrMore)


class Event(PageNode):
    '''A historical event: war, battle, fall of a kingdom, etc.'''

    __label__ = 'Event'

    entity_type = StringProperty(db_property='type')
    start_date = StringProperty()
    end_date = StringProperty()
    casualties = StringProperty()
    notable_for = StringProperty()

    took_place_in = RelationshipTo(
        'Location',
        'TOOK_PLACE_IN',
        cardinality=ZeroOrMore,
    )
    part_of = RelationshipTo('Event', 'PART_OF', cardinality=ZeroOrMore)
    occurred_during = RelationshipTo(
        'Timeline',
        'OCCURRED_DURING',
        cardinality=ZeroOrMore,
    )


class Organization(PageNode):
    '''An order, army, house, or a political unit'''

    __label__ = 'Organization'

    entity_type = StringProperty(db_property='type')
    founded_date = StringProperty()
    dissolved_date = StringProperty()
    clothing = StringProperty()
    weaponry = StringProperty()
    purpose = StringProperty()
    notable_for = StringProperty()

    based_in = RelationshipTo('Location', 'BASED_IN', cardinality=ZeroOrMore)


class Timeline(PageNode):
    '''A historical age or era, e.g. Third Age'''

    __label__ = 'Timeline'

    start_date = StringProperty()
    end_date = StringProperty()
    abbreviation = StringProperty()


class Item(PageNode):
    '''An artifact or object of significance (weapons, rings, etc.)'''

    __label__ = 'Item'

    entity_type = StringProperty(db_property='type')
    material = StringProperty()
    notable_for = StringProperty()


class Language(PageNode):
    '''A language of Middle-earth'''

    __label__ = 'Language'

    family = StringProperty()

    spoken_by = RelationshipTo('Race', 'SPOKEN_BY', cardinality=ZeroOrMore)
    spoken_in = RelationshipTo('Location', 'SPOKEN_IN', cardinality=ZeroOrMore)
    written_in = RelationshipTo('Script', 'WRITTEN_IN', cardinality=ZeroOrMore)


class Script(PageNode):
    '''A writing system of Middle-earth'''

    __label__ = 'Script'
