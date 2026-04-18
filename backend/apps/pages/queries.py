# Maps Neo4j node label to API entity-type string
LABEL_TO_TYPE: dict[str, str] = {
    'Character': 'character',
    'Race': 'race',
    'Location': 'location',
    'Event': 'event',
    'Organization': 'organization',
    'Timeline': 'timeline',
    'Item': 'item',
    'Language': 'language',
    'Script': 'script',
}


# Label that don't carry type information (shared by all subtypes)
_SYSTEM_LABELS: frozenset[str] = frozenset({'Page'})


def labels_to_type(labels: list[str]) -> str | None:
    '''Returns the entity-type string for a list of Neo4j node labels'''

    for label in labels:
        if label in LABEL_TO_TYPE:
            return LABEL_TO_TYPE[label]

    return None


# Attribute metadata

# Per entity-type: tuple of Neo4j property names that forms the
# 'attributes' dict in the API response.
# 'slug' and 'names' are alway top-level, never inside attributes
_TYPE_ATTR_KEYS: dict[str, tuple[str, ...]] = {
    'character': (
        'titles', 'gender', 'birthDate', 'deathDate', 'hair', 'eyes', 'height',
        'weapon', 'clothing', 'notableFor',
    ),
    'race': (
        'lifespan', 'avgHeight', 'hair', 'eyes', 'skin', 'weaponry',
        'clothing', 'distinctions',
    ),
    'location': (
        'type', 'population', 'creationDate', 'destructionDate', 'notableFor',
    ),
    'event': (
        'type', 'startDate', 'endDate', 'casualties', 'notableFor',
    ),
    'organization': (
        'type', 'foundedDate', 'dissolvedDate', 'clothing', 'weaponry',
        'purpose', 'notableFor',
    ),
    'timeline': (
        'startDate', 'endDate', 'abbreviation',
    ),
    'item': (
        'type', 'material', 'notableFor',
    ),
    'language': (
        'family',
    ),
    'script': (),
}


# Location / Event / organization / Item all use the bare 'type' property
# in Neo4j. Rename it to a descriptive API key in the GET response.
_TYPE_PROP_RENAME: dict[str, dict[str, str]] = {
    'location': {'type': 'locationType'},
    'event': {'type': 'eventType'},
    'organization': {'type': 'organizationType'},
    'item': {'type': 'itemType'},
}


# Reverse mappings: API attribute name to Neo4j property name.
# Used in PATCH to convert the incoming JSON to DB column names.
_ATTR_API_TO_DB: dict[str, dict[str, str]] = {
    'location': {'locationType': 'type'},
    'event': {'eventType': 'type'},
    'organization': {'organizationType': 'type'},
    'item': {'itemType': 'type'},
}


def build_attributes_for_response(props: dict, entity_type: str) -> dict:
    '''
    Extract and rename entity-specific attributes
    from raw Neo4j node properties from the GET response.

    Unknown keys (not in the whitelist for this type) are silently dropped.
    Missing keys are returned as None.
    '''

    keys = _TYPE_ATTR_KEYS.get(entity_type, ())
    rename = _TYPE_PROP_RENAME.get(entity_type, {})

    return {rename.get(key, key): props.get(key) for key in keys}


def normalize_patch_attributes(raw_attrs: dict, entity_type: str) -> dict:
    '''
    Convert API attribute names to Neo4j property names for SET p += $attrs.

    - Unknown/invalid keys for this entity types are silently dropped (prevents
        arbitrary property injection into the node)
    - Handles the locationType -> type rename and similar
    '''

    allowed_db_keys: frozenset[str] = frozenset(
        _TYPE_ATTR_KEYS.get(entity_type, ())
    )
    api_to_db = _ATTR_API_TO_DB.get(entity_type, {})

    result: dict = {}
    for api_key, value in raw_attrs.items():
        db_key = api_to_db.get(api_key, api_key)

        if db_key in allowed_db_keys:
            result[db_key] = value

    return result


# Relation metadata

# Whitelist of allowed relationship types for PATCH /pages/{slug}/.
# Relationship-type names are interpolated into Cypher strings.
# Only whitelisted names may be used. This prevents Cypher injections.
ALLOWED_REL_TYPES: frozenset[str] = frozenset({
    # Character
    'OF_RACE',
    'BORN_IN',
    'DIED_IN',
    'DWELLED_IN',
    'SPEAKS',
    'CHILD_OF',
    'MARRIED_TO',
    'SIBLING_OF',
    'PARTICIPATED_IN',
    'LIVED_DURING',
    'RULED',
    'MEMBER_OF',
    'WIELDS',
    'OWNS',
    'BORE',
    'CRAFTED',
    # Race
    'SUBRACE_OF',
    'INHABITS',
    # Location
    'REGION_OF',
    # Event
    'TOOK_PLACE_IN',
    'PART_OF',
    'OCCURRED_DURING',
    # Organization
    'BASED_IN',
    # Language
    'SPOKEN_BY',
    'SPOKEN_IN',
    'WRITTEN_IN',
})


# Read query

# Retrieves all data for a single wiki page in one round trip.
# CALL subqueris prevent Cartesian products that would arise if we used
# multiple top-level OPTIONAL MATCHes that each expands to many rows.
#
# Parameters:
#   $slug - public page identifier
#   $user_id - Django user PK (int) or null for anonymous users
PAGE_DETAIL_QUERY = '''\
MATCH (p:Page {slug: $slug})
    OPTIONAL MATCH (p)-[:HAS_ARTICLE]->(a:Article)

CALL {
    WITH p
    OPTIONAL MATCH (p)-[:IN_CATEGORY]->(cat:Category)
    WITH cat WHERE cat IS NOT NULL
    RETURN collect({slug: cat.slug, name: cat.name}) AS categories
}

CALL {
    WITH p
    OPTIONAL MATCH (p)-[out_rel]->(target:Page)
    WITH target, out_rel WHERE target IS NOT NULL
    OPTIONAL MATCH (target)-[:HAS_ARTICLE]->(ta:Article)
    RETURN collect({
        relType: type(out_rel),
        targetSlug: target.slug,
        targetNames: target.names,
        targetLabels: labels(target),
        targetImageUrl: ta.imageUrl,
        relProps: properties(out_rel)
    }) AS outgoing_rels
}

CALL {
    WITH p
    OPTIONAL MATCH (source:Page)-[in_rel]->(p)
    WITH source, in_rel WHERE source IS NOT NULL
    OPTIONAL MATCH (source)-[:HAS_ARTICLE]->(sa:Article)
    RETURN collect({
        relType: type(in_rel),
        sourceSlug: source.slug,
        sourceNames: source.names,
        sourceLabels: labels(source),
        sourceImageUrl: sa.imageUrl,
        relProps: properties(in_rel)
    }) AS incoming_rels
}

CALL {
    WITH p
    OPTIONAL MATCH (u:User)-[:LIKED]->(p)
    RETURN count(u) AS likes_count
}

CALL {
    WITH p
    OPTIONAL MATCH (comment:Comment)-[:ON]->(p)
    RETURN count(comment) AS comments_count
}

RETURN
    properties(p) AS props,
    labels(p) AS node_labels,
    properties(a) AS article_props,
    categories,
    outgoing_rels,
    incoming_rels,
    likes_count,
    comments_count,
    CASE
        WHEN $user_id IS NOT NULL
        THEN EXISTS {
            MATCH (:User {django_id: $user_id})-[LIKED]->(p)
        }
        ELSE null
    END as is_liked
'''


# Update queries

# Partial node property update.
# SET p += $attrs merges the map - existing properties not in attrs are left
# untouched.
PAGE_ATTRS_UPDATE_QUERY = '''\
MATCH (p:Page {slug: $slug})
SET p += $attrs
'''

# Upsert article node connected to the page.
# MERGE ensures we never create duplicate articles.
# ON CREATE sets the creation timestamp only once.
PAGE_ARTICLE_UPSERT_QUERY = '''\
MATCH (p:Page {slug: $slug})
MERGE (p)-[:HAS_ARTICLE]->(a:Article)
ON CREATE SET a.createdAt = datetime()
SET a.imageUrl = $image_url, a.text = $text, a.updatedAt = datetime()
'''

# Replace all categories for a page atomically.
# WITH DISTINCT p after DELETE prevents Cartesian product when page
# originally had multiple categories
PAGE_CATEGORIES_REPLACE_QUERY = '''\
MATCH (p:Page {slug: $slug})
    OPTIONAL MATCH (p)-[r:IN_CATEGORY]->()
DELETE r
WITH DISTINCT p
UNWIND $cat_slugs AS cat_slug
MATCH (cat:Category {slug: cat_slug})
MERGE (p)-[:IN_CATEGORY]->(cat)
'''

# Delete all outgoing relations of a specific type from a page.
# rel_type is string-interplated ONLY after whitelist validation in services.py
PAGE_RELS_DELETE_TEMPLATE = '''\
MATCH (p:Page {{slug: $slug}})-[r:{rel_type}]->()
DELETE r
'''

# Create new outgoing relations of a specific type.
# SET r = t.properties sets all relation properties from the provided map.
# rel_type is string-interplated ONLY after whitelist validation in services.py
PAGE_RELS_CREATE_TEMPLATE = """\
MATCH (p:Page {{slug: $slug}})
WITH p
UNWIND $targets AS t
MATCH (target:Page {{slug: t.slug}})
CREATE (p)-[r:{rel_type}]->(target)
SET r = t.properties
"""

# DETACH DELETE the page and its article node.
# DETACH removes all edges from/to the page automatically.
# We additionally delete the orphaned Article node to avoid graph litter.
PAGE_DELETE_QUERY = """\
MATCH (p:Page {slug: $slug})
OPTIONAL MATCH (p)-[:HAS_ARTICLE]->(a:Article)
DETACH DELETE p, a
"""
