"""
Cypher query constants and type metadata for the pages app.

Property naming convention in Neo4j (set by catalog CREATE queries):
  - camelCase for multi-word props: birthDate, deathDate, notableFor, etc.
  - bare 'type' for entity-type discriminator in Location / Event /
    Organization / Item (db_property='type' in neomodel models).
  - 'slug' and 'names' are shared by all :Page subtypes.

Security note - relationship type interpolation:
  Cypher does not support parameterised relationship type names.
  PAGE_RELS_DELETE_TEMPLATE and PAGE_RELS_CREATE_TEMPLATE use Python
  str.format() to interpolate the rel type.  This is safe ONLY because
  services.py validates the value against ALLOWED_REL_TYPES before calling
  .format().  Never interpolate user input here without that check.
"""


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

# Resolve entity type by slug. Return labels list or empty if not found
PAGE_FETCH_LABELS_QUERY = '''\
MATCH (p:Page {slug: $slug})
RETURN labels(p) AS labels
LIMIT 1
'''

# Retrieves all data for a single wiki page in one round trip.
# CALL {} subqueris prevent Cartesian products that would arise if we used
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
            MATCH (:User {django_id: $user_id})-[:LIKED]->(p)
        }
        ELSE null
    END as is_liked
'''


# Validation queries

# Batch-check whether :Page nodes with given slugs exist.
# Returns one row per input slug: (slug, exists_bool).
# Used to validate target slugs in PATCH /pages/{slug}/ relations BEFORE
# starting the write transaction so missing slugs surface as 400,
# not silent data loss
PAGE_SLUGS_EXIST_QUERY = '''\
WITH $slugs AS all_slugs
UNWIND all_slugs AS slug
OPTIONAL MATCH (p:Page {slug: slug})
RETURN slug, p IS NOT NULL AS exists
'''

# Same for :Category nodes.
# Used to validate categories list in PATCH
CATEGORY_SLUGS_EXISTS_QUERY = '''\
WITH $slugs AS all_slugs
UNWIND all_slugs AS slug
OPTIONAL MATCH (c:Category {slug: slug})
RETURN slug, c IS NOT NULL AS exists
'''


# Write queries

# Replace the `names` array on a page node.
PAGE_NAMES_UPDATE_QUERY = '''\
MATCH (p:Page {slug: $slug})
SET p.names = $names
'''

# Update queries

# Partial node property update.
# SET p += $attrs merges the map - existing properties not in attrs are left
# untouched.
PAGE_ATTRS_UPDATE_QUERY = '''\
MATCH (p:Page {slug: $slug})
SET p += $attrs
'''

# Create or update the article node attached to a page.
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


PAGE_CATEGORIES_CLEAR_QUERY = '''\
MATCH (p:Page {slug: $slug})-[r:IN_CATEGORY]->()
DELETE r
'''


# Delete all outgoing relations of a specific type from a page.
# rel_type is string-interplated ONLY after whitelist validation in services.py
# str.format() is called on this template.
PAGE_RELS_OUTGOING_DELETE_TEMPLATE = '''\
MATCH (p:Page {{slug: $slug}})-[r:{rel_type}]->()
DELETE r
'''

# Create new outgoing relations of a specific type.
# SET r = t.properties sets all relation properties from the provided map.
# rel_type is string-interplated ONLY after whitelist validation in services.py
# str.format() is called on this template.
PAGE_RELS_OUTGOING_CREATE_TEMPLATE = '''\
MATCH (p:Page {{slug: $slug}})
UNWIND $targets AS t
MATCH (target:Page {{slug: t.slug}})
CREATE (p)-[r:{rel_type}]->(target)
SET r = t.properties
'''

PAGE_RELS_INCOMING_DELETE_TEMPLATE = '''\
MATCH ()-[r:{rel_type}]->(p:Page {{slug: $slug}})
DELETE r
'''

PAGE_RELS_INCOMING_CREATE_TEMPLATE = '''\
MATCH (p:Page {{slug: $slug}})
UNWIND $sources AS s
MATCH (source:Page {{slug: s.slug}})
CREATE (source)-[r:{rel_type}]->(p)
SET r = s.properties
'''

# DETACH DELETE the page and its article node.
# DETACH removes all edges from/to the page automatically.
# We additionally delete the orphaned Article node to avoid graph litter.
# RETURN 1 allows detecting "not found" (0 rows) vs "deleted" (1 row)
# in a single round-trip.
PAGE_DELETE_QUERY = '''\
MATCH (p:Page {slug: $slug})
OPTIONAL MATCH (p)-[:HAS_ARTICLE]->(a:Article)
DETACH DELETE p, a
RETURN 1 AS deleted
'''


# Like queries

# Both queries use MERGE so they are naturally idempotent
# count(liker) counts non-null matches inly, so it correctly returns 0
# when there are no likes (unlike count(*))

# Idempotent like.  Creates UserRef if it doesn't exist yet.
# Parameters: $slug (str), $user_id (int).
PAGE_LIKE_ADD_QUERY = '''\
MATCH (p:Page {slug: $slug})
MERGE (u:User {django_id: $user_id})
WITH p, u
MERGE (u)-[r:LIKED]->(p)
ON CREATE SET r.created_at = datetime()
WITH p
OPTIONAL MATCH (liker:User)-[:LIKED]->(p)
RETURN count(liker) AS likes_count, true AS is_liked
'''

# Idempotent unlike.  No-op if the user never liked the page.
# Parameters: $slug (str), $user_id (int).
PAGE_LIKE_REMOVE_QUERY = '''\
MATCH (p:Page {slug: $slug})
    OPTIONAL MATCH (u:User {django_id: $user_id})-[r:LIKED]->(p)
DELETE r
WITH p
OPTIONAL MATCH (liker:User)-[:LIKED]->(p)
RETURN count(liker) AS likes_count, false AS is_liked
'''
