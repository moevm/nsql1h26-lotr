"""
Cypher query constants for the analytics app.

Design notes:
    All queries are read-only (MATCH only, no writes).

top_connected
    We count only lore relationships - (LIKED, WROTE, ON, IN_CATEGORY, HAS_ARTICLE,
    SUBCATEGORY_OF) are excluded so the ranking reflects narrative significance,
    not user activity.

most_liked / most_commented
    Both return a `labels` column containing the full Neo4j label list for the page
    (e.g. ['Page', 'Character']).  The service strips 'Page' to produce the
    entity_type field.

characters_by_race
    A character with no OF_RACE relationship is excluded
    (MATCH, not OPTIONAL MATCH) - unknown race characters don't pollute the chart.
"""

from dataclasses import dataclass
from typing import Literal
from apps.pages.enums import SocRelTypes

from .constants import MOST_COMMENTED_LIMIT, MOST_LIKED_LIMIT

# Global statistics endpoint

# Counts

# RETURN
#     count(p) AS total,
#     count(p:Character) AS characters,
#     count(p:Race) AS races,
#     ...
# does not work for some reason - always returns {total, total, total, ...}.
# May be a quirk of Neo4j??
COUNTS_QUERY = """\
MATCH (n:Page)
RETURN
    sum(CASE WHEN n:Character THEN 1 ELSE 0 END) AS characters,
    sum(CASE WHEN n:Race THEN 1 ELSE 0 END) AS races,
    sum(CASE WHEN n:Location THEN 1 ELSE 0 END) AS locations,
    sum(CASE WHEN n:Event THEN 1 ELSE 0 END) AS events,
    sum(CASE WHEN n:Organization THEN 1 ELSE 0 END) AS organizations,
    sum(CASE WHEN n:Timeline THEN 1 ELSE 0 END) AS timelines,
    sum(CASE WHEN n:Item THEN 1 ELSE 0 END) AS items,
    sum(CASE WHEN n:Language THEN 1 ELSE 0 END) AS languages,
    sum(CASE WHEN n:Script THEN 1 ELSE 0 END) AS scripts
"""


# Entity by property

CHARACTERS_BY_RACE_QUERY = """\
MATCH (c:Character)-[:OF_RACE]->(r:Race)
RETURN
    r.slug AS slug,
    r.names[0] AS name,
    count(c) AS count
ORDER BY count DESC, name ASC
"""

CHARACTERS_BY_GENDER_QUERY = """\
MATCH (c:Character)
RETURN
    coalesce(c.gender, 'unknown') AS gender,
    count(c) AS count
ORDER BY count DESC
"""

CHARACTERS_BY_IS_ALIVE_COUNT_QUERY = """\
MATCH (c:Character)
RETURN
    count(CASE WHEN c.deathDate IS NULL THEN 1 END) AS alive,
    count(CASE WHEN c.deathDate IS NOT NULL THEN 1 END) AS deceased
"""

EVENTS_BY_TIMELINE_QUERY = """\
MATCH (e:Event)-[:OCCURRED_DURING]->(t:Timeline)
WITH t, count(e) AS event_count
ORDER BY event_count DESC
RETURN
    t.slug AS timeline_slug,
    t.names[0] AS name,
    event_count AS count
"""

LOCATIONS_BY_TYPE_QUERY = """\
MATCH (l:Location)
WHERE l.type IS NOT NULL
RETURN l.type AS type, count(l) AS count
ORDER BY count DESC
"""

ITEMS_BY_TYPE_QUERY = """\
MATCH (i:Item)
WHERE i.type IS NOT NULL
RETURN i.type AS type, count(i) AS count
ORDER BY count DESC
"""

# Top connected

_TOP_CONNECTED_TEMPLATE = """\
MATCH (n:{label})
WITH n,
     size([(n)-[r]-() WHERE NOT type(r) IN {excluded} | r]) AS connections
ORDER BY connections DESC, n.names[0] ASC
LIMIT 5
RETURN n.slug AS slug, n.names[0] AS name, connections AS connections_count
"""


def top_connected_query(label: str) -> str:
    """Build a top-connected query for the given :Page sub-label."""
    return _TOP_CONNECTED_TEMPLATE.format(
        label=label,
        excluded=f'[{", ".join("'" + str(x) + "'" for x in SocRelTypes)}]',
    )


TOP_CONNECTED_LABELS = [
    'Character',
    'Race',
    'Location',
    'Event',
    'Organization',
    'Timeline',
    'Item',
    'Language',
    'Script',
]


# Most liked

MOST_LIKED_QUERY = f"""\
MATCH (:User)-[:LIKED]->(p:Page)
WITH p, count(*) AS likes_count
ORDER BY likes_count DESC
LIMIT {MOST_LIKED_LIMIT}
RETURN
    p.slug AS slug,
    p.names[0] AS name,
    labels(p) AS lbls,
    likes_count AS count
"""

MOST_COMMENTED_QUERY = f"""\
MATCH (c:Comment)-[:ON]->(p:Page)
WITH p, count(c) AS comment_count
ORDER BY comment_count DESC
LIMIT {MOST_COMMENTED_LIMIT}
RETURN
    p.slug AS slug,
    p.names[0] AS name,
    labels(p) AS lbls,
    comment_count AS count
"""


# Neighbors endpoint


NEIGHBORS_ROOT_QUERY = """\
MATCH (root:Page {slug: $slug})
OPTIONAL MATCH (root)-[:HAS_ARTICLE]->(a:Article)
RETURN
    root.slug AS slug,
    root.names AS names,
    labels(root) AS node_labels,
    a.imageUrl AS image_url
LIMIT 1
"""


# TODO: switch from formatting depth to apoc procedures
# Parameters:
#   $slug - root page slug (string)
#   $node_labels - list of Neo4j labels to accept as neighbors, or null for all
#   $limit - maximum number of distinct neighbor nodes to return (integer)
#   depth - maximum traversal depth: 1 or 2 (integer), formatted into query, because
#       Neo4j does not allow [*1..$depth]
NEIGHBORS_NODES_TEMPLATE = """\
MATCH (root:Page {{slug: $slug}})
MATCH path = (root)-[*1..{depth}]-(nb:Page)
WHERE nb <> root
    AND ALL(n IN nodes(path) WHERE n:Page)
    AND (
        $node_labels IS NULL
        OR ALL(n IN nodes(path) WHERE
            n = root
            OR any(lbl IN labels(n) WHERE lbl IN $node_labels)
        )
    )
    AND (
        $rel_types IS NULL
        OR ALL(r IN relationships(path) WHERE type(r) IN $rel_types)
    )
WITH DISTINCT nb
LIMIT $limit
OPTIONAL MATCH (nb)-[:HAS_ARTICLE]->(a:Article)
RETURN
    nb.slug AS slug,
    nb.names AS names,
    labels(nb) AS node_labels,
    a.imageUrl AS image_url
"""


# Parameters:
#   $slugs - list of page slugs to use as the node set (root + neighbors)
#   $rel_types - list of relationship type strings to include, or null for all
#
# Directed match avoids returning duplicate rows for the same underlying
# relationship.  The direction information (from/to) is preserved in the
# response so the frontend can render arrows correctly if needed.
NEIGHBORS_EDGES_QUERY = """\
MATCH (a:Page)-[r]->(b:Page)
WHERE a.slug IN $slugs
    AND b.slug IN $slugs
    AND ($rel_types IS NULL OR type(r) IN $rel_types)
RETURN
    a.slug AS from_slug,
    b.slug AS to_slug,
    type(r) AS rel_type,
    properties(r) AS rel_properties
"""


# Shortest path endpoint


# Parameters:
#   $from_slug - slug of the start page (string)
#   $to_slug - slug of the end page (string)
#   $node_labels - list of Neo4j labels to allow on intermediate path nodes,
#       or null for all :Page node types
#   $rel_types - list of relationship type strings; path is rejected if any
#       relationship is not in this list; null means all types allowed
#   max_depth - maximum traversal depth, 1–15; formatted into query, because
#       Neo4j does not allow [*1..$depth]
SHORTEST_PATH_TEMPLATE = """\
MATCH (a:Page {{slug: $from_slug}})
WITH a
MATCH (b:Page {{slug: $to_slug}})
WITH a, b
MATCH path = shortestPath((a)-[*1..{max_depth}]-(b))
WITH path, relationships(path) AS rels, nodes(path) AS ns
WHERE ALL(n IN ns WHERE
    n = a
    OR n = b
    OR (n:Page
        AND (
            $node_labels IS NULL
            OR ANY(lbl IN labels(n) WHERE lbl IN $node_labels)
        )
    )
)
    AND ($rel_types IS NULL
        OR ALL(r IN rels WHERE type(r) IN $rel_types))
RETURN
    [n IN ns | {{slug: n.slug, names: n.names, node_labels: labels(n)}}] AS path_nodes,
    [r IN rels | {{rel_type: type(r), rel_properties: properties(r)}}] AS path_rels
"""


# Fetch image URLs for a batch of page slugs in a single round-trip.
# Used to enrich path nodes after the main shortest-path query.
# Parameters:
#   $slugs - list of page slugs (strings)
PAGE_BATCH_IMAGES_QUERY = """\
MATCH (n:Page)-[:HAS_ARTICLE]->(a:Article)
WHERE n.slug IN $slugs
RETURN n.slug AS slug, a.imageUrl AS image_url
"""


# Custom analytics endpoint


@dataclass
class _AttrDef:
    # prop - scalar attribute
    # bool - computed bool attribute
    # rel - relation attribute (graph traversal)
    mode: Literal['prop', 'bool', 'rel']

    # Cypher expression
    # For prop/bool: {a} -> main entity alias
    # For rel: {v} -> target-node
    expr: str

    # OPTIONAL MATCH clause (rel mode only)
    # {a} -> main alias, {v} -> target-node alias
    optional_match: str | None = None

    @property
    def is_rel(self) -> bool:
        return self.mode == 'rel'


# Atlas of allowed (entity_type, attr) combinations
# Adding new attrs here is sufficient; no other file needs changing.
ATTR_DEFS: dict[str, dict[str, _AttrDef]] = {
    'character': {
        'gender': _AttrDef(
            mode='prop',
            expr="coalesce({a}.gender, 'unknown')",
        ),
        'race': _AttrDef(
            mode='rel',
            expr='{v}.names[0]',
            optional_match='OPTIONAL MATCH ({a})-[:OF_RACE]->({v}:Race)',
        ),
        'is_alive': _AttrDef(
            mode='bool',
            expr="CASE WHEN {a}.deathDate IS NULL THEN 'alive' ELSE 'deceased' END",
        ),
        'organization': _AttrDef(
            mode='rel',
            expr='{v}.names[0]',
            optional_match='OPTIONAL MATCH ({a})-[:MEMBER_OF]->({v}:Organization)',
        ),
        'timeline': _AttrDef(
            mode='rel',
            expr='{v}.names[0]',
            optional_match='OPTIONAL MATCH ({a})-[:LIVED_DURING]->({v}:Timeline)',
        ),
    },
    'location': {
        'entity_type': _AttrDef(
            mode='prop',
            expr="coalesce({a}.type, 'unknown')",
        ),
        'is_destroyed': _AttrDef(
            mode='bool',
            expr=(
                "CASE WHEN {a}.destructionDate IS NOT NULL THEN 'destroyed' "
                "ELSE 'standing' END"
            ),
        ),
    },
    'event': {
        'entity_type': _AttrDef(
            mode='prop',
            expr="coalesce({a}.type, 'unknown')",
        ),
        'timeline': _AttrDef(
            mode='rel',
            expr='{v}.names[0]',
            optional_match='OPTIONAL MATCH ({a})-[:OCCURRED_DURING]->({v}:Timeline)',
        ),
    },
    'organization': {
        'entity_type': _AttrDef(
            mode='prop',
            expr="coalesce({a}.type, 'unknown')",
        ),
        'is_dissolved': _AttrDef(
            mode='bool',
            expr=(
                "CASE WHEN {a}.dissolvedDate IS NOT NULL THEN 'dissolved' "
                "ELSE 'active' END"
            ),
        ),
    },
    'item': {
        'entity_type': _AttrDef(
            mode='prop',
            expr="coalesce({a}.type, 'unknown')",
        ),
        'material': _AttrDef(
            mode='prop',
            expr="coalesce({a}.material, 'unknown')",
        ),
    },
}


# Cypher alias and Neo4j label per entity_type.
# Must stay in sync with catalogs/filters.py aliases.
_ENTITY_ALIAS: dict[str, str] = {
    'character': 'c',
    'race': 'r',
    'location': 'l',
    'event': 'e',
    'organization': 'o',
    'timeline': 't',
    'item': 'i',
    'language': 'lang',
    'script': 's',
}

_ENTITY_LABEL: dict[str, str] = {
    'character': 'Character',
    'race': 'Race',
    'location': 'Location',
    'event': 'Event',
    'organization': 'Organization',
    'timeline': 'Timeline',
    'item': 'Item',
    'language': 'Language',
    'script': 'Script',
}


# Internal helpers


def _resolve(template: str, alias: str, var: str) -> str:
    '''Substitute {a} and {v} placeholders in a template string.'''
    return template.replace('{a}', alias).replace('{v}', var)


def _build_x_block(
    attr_def: _AttrDef,
    alias: str,
) -> tuple[str, str]:
    '''
    Return (optional_match_clause, x_expr) for the x axis.

    For REL attrs: returns the OPTIONAL MATCH line and an expression referencing _xnode.
    For PROP/BOOL attrs: returns empty string and the inline expression.
    '''
    if attr_def.is_rel and attr_def.optional_match is not None:
        optional_match = _resolve(attr_def.optional_match, alias, '_xnode')
        x_expr = _resolve(attr_def.expr, alias, '_xnode')
        return optional_match, x_expr
    else:
        return '', _resolve(attr_def.expr, alias, '')


def _build_g_block(
    group_def: _AttrDef,
    alias: str,
) -> tuple[str, str]:
    '''
    Return (optional_match_clause, g_expr) for the group_by axis.

    Only REL group_by attrs need an OPTIONAL MATCH.
    '''
    if group_def.is_rel and group_def.optional_match is not None:
        optional_match = _resolve(group_def.optional_match, alias, '_gnode')
        g_expr = _resolve(group_def.expr, alias, '_gnode')
        return optional_match, g_expr
    else:
        return '', _resolve(group_def.expr, alias, '')


# Public query builders


def build_simple_query(
    entity_type: str,
    attr: str,
    filter_where: str,
) -> str:
    '''
    Build the Cypher query for the simple (no group_by) case.

    Parameters injected at runtime by the caller:
        $top_n - LIMIT value
        + all params produced by the filter's to_cypher_where()
    '''
    alias = _ENTITY_ALIAS[entity_type]
    label = _ENTITY_LABEL[entity_type]
    attr_def = ATTR_DEFS[entity_type][attr]

    optional_match, x_expr = _build_x_block(attr_def, alias)

    if attr_def.is_rel:
        return f'''\
            MATCH ({alias}:{label})
            {filter_where}
            WITH {alias}
            {optional_match}
            WITH {alias}, {x_expr} AS x
            WHERE x IS NOT NULL
            RETURN x, count({alias}) AS value
            ORDER BY value DESC, x ASC
            LIMIT $top_n
        '''
    else:
        return f'''\
            MATCH ({alias}:{label})
            {filter_where}
            RETURN {x_expr} AS x, count({alias}) AS value
            ORDER BY value DESC, x ASC
            LIMIT $top_n
        '''


def build_grouped_query(
    entity_type: str,
    attr: str,
    group_by: str,
    filter_where: str,
) -> str:
    '''
    Build the Cypher query for the grouped (with group_by) case.

    No LIMIT here - the caller receives ALL (x, g, value) rows and
    applies top_n filtering after pivoting in Python.
    A hard safety cap of 2 000 rows is applied to prevent runaway results.

    Constraint: ATTR_DEFS[entity_type][attr].is_rel
                and ATTR_DEFS[entity_type][group_by].is_rel
                must NOT both be True (caller validates this).
    '''
    alias = _ENTITY_ALIAS[entity_type]
    label = _ENTITY_LABEL[entity_type]
    attr_def = ATTR_DEFS[entity_type][attr]
    group_def = ATTR_DEFS[entity_type][group_by]

    optional_match_x, x_expr = _build_x_block(attr_def, alias)
    optional_match_g, g_expr = _build_g_block(group_def, alias)

    lines = [f'MATCH ({alias}:{label})', filter_where]

    if attr_def.is_rel:
        lines += [
            f'WITH {alias}',
            optional_match_x,
            f'WITH {alias}, {x_expr} AS x',
            'WHERE x IS NOT NULL'
        ]
        if group_def.is_rel:
            # Both REL - caller must have raised 400 before reaching here.
            # Defensive guard.
            raise AssertionError('Both attr and group_by are REL - must be rejected upstream.')
        lines.append(f'RETURN x, {g_expr} AS g, count({alias}) AS value')
    else:
        # attr is PROP or BOOL
        if group_def.is_rel:
            lines += [
                f'WITH {alias}',
                optional_match_g
            ]
            lines.append(f'RETURN {x_expr} AS x, {g_expr} AS g, count({alias}) AS value')
        else:
            lines.append(f'RETURN {x_expr} AS x, {g_expr} AS g, count({alias}) AS value')

    lines += [
        'ORDER BY x ASC, value DESC',
        'LIMIT 2000'
    ]
    return '\n'.join(lines)
