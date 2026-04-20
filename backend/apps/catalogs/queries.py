# Character
# Uses OPTIONAL_MATCH for JOIN-filters and for output.

CHARACTER_LIST_QUERY = """\
MATCH (c:Character)
    OPTIONAL MATCH (c)-[:OF_RACE]->(race:Race)
    OPTIONAL MATCH (c)-[:BORN_IN]->(born_loc:Location)
WITH c, race, born_loc
{where}
ORDER BY {order_by}
SKIP $skip
LIMIT $limit
RETURN
    c.slug AS slug,
    c.names AS names,
    c.titles AS titles,
    c.gender AS gender,
    c.birthDate AS birth_date,
    c.deathDate AS death_date,
    c.hair AS hair,
    c.eyes AS eyes,
    c.height AS height,
    c.weapon AS weapon,
    c.clothing AS clothing,
    c.notableFor AS notable_for,
    race.slug AS race_slug,
    race.names[0] AS race_name,
    born_loc.slug AS born_in_slug,
    born_loc.names[0] AS born_in_name
"""

CHARACTER_COUNT_QUERY = """\
MATCH (c:Character)
    OPTIONAL MATCH (c)-[:OF_RACE]->(race:Race)
    OPTIONAL MATCH (c)-[:BORN_IN]->(born_loc:Location)
WITH c, race, born_loc
{where}
RETURN count(c) AS total
"""

# Whitelist for sort field: API param -> Cypher expression
CHARACTER_SORT_FIELDS: dict[str, str] = {
    "name": "c.names[0]",
    "gender": "c.gender",
    "birth_date": "c.birthDate",
    "death_date": "c.deathDate",
}
CHARACTER_DEFAULT_SORT = "c.names[0] ASC"

# Race

RACE_LIST_QUERY = """\
MATCH (r:Race)
{where}
ORDER BY {order_by}
SKIP $skip
LIMIT $limit
RETURN
    r.slug AS slug,
    r.names AS names,
    r.lifespan AS lifespan,
    r.avgHeight AS avg_height,
    r.hair AS hair,
    r.eyes AS eyes,
    r.skin AS skin,
    r.weaponry AS weaponry,
    r.clothing AS clothing,
    r.distinctions AS distinctions
"""

RACE_COUNT_QUERY = """\
MATCH (r:Race)
{where}
RETURN count(r) AS total
"""

RACE_SORT_FIELDS: dict[str, str] = {
    "name": "r.names[0]",
    "lifespan": "r.lifespan",
}
RACE_DEFAULT_SORT = "r.names[0] ASC"

# Location

LOCATION_LIST_QUERY = """\
MATCH (l:Location)
{where}
ORDER BY {order_by}
SKIP $skip
LIMIT $limit
RETURN
    l.slug AS slug,
    l.names AS names,
    l.type AS entity_type,
    l.population AS population,
    l.creationDate AS creation_date,
    l.destructionDate AS destruction_date,
    l.notableFor AS notable_for
"""

LOCATION_COUNT_QUERY = """\
MATCH (l:Location)
{where}
RETURN count(l) AS total
"""

LOCATION_SORT_FIELDS: dict[str, str] = {
    "name": "l.names[0]",
    "entity_type": "l.type",
    "creation_date": "l.creationDate",
}
LOCATION_DEFAULT_SORT = "l.names[0] ASC"

# Event

EVENT_LIST_QUERY = """\
MATCH (e:Event)
{where}
ORDER BY {order_by}
SKIP $skip
LIMIT $limit
RETURN
    e.slug AS slug,
    e.names AS names,
    e.type AS entity_type,
    e.startDate AS start_date,
    e.endDate AS end_date,
    e.casualties AS casualties,
    e.notableFor AS notable_for
"""

EVENT_COUNT_QUERY = """\
MATCH (e:Event)
{where}
RETURN count(e) AS total
"""

EVENT_SORT_FIELDS: dict[str, str] = {
    "name": "e.names[0]",
    "entity_type": "e.type",
    "start_date": "e.startDate",
    "end_date": "e.endDate",
}
EVENT_DEFAULT_SORT = "e.names[0] ASC"

# Organization

ORGANIZATION_LIST_QUERY = """\
MATCH (o:Organization)
{where}
ORDER BY {order_by}
SKIP $skip
LIMIT $limit
RETURN
    o.slug AS slug,
    o.names AS names,
    o.type AS entity_type,
    o.foundedDate AS founded_date,
    o.dissolvedDate AS dissolved_date,
    o.clothing AS clothing,
    o.weaponry AS weaponry,
    o.purpose AS purpose,
    o.notableFor AS notable_for
"""

ORGANIZATION_COUNT_QUERY = """\
MATCH (o:Organization)
{where}
RETURN count(o) AS total
"""

ORGANIZATION_SORT_FIELDS: dict[str, str] = {
    "name": "o.names[0]",
    "entity_type": "o.type",
    "founded_date": "o.foundedDate",
}
ORGANIZATION_DEFAULT_SORT = "o.names[0] ASC"

# Timeline

TIMELINE_LIST_QUERY = """\
MATCH (t:Timeline)
{where}
ORDER BY {order_by}
SKIP $skip
LIMIT $limit
RETURN
    t.slug AS slug,
    t.names AS names,
    t.startDate AS start_date,
    t.endDate AS end_date,
    t.abbreviation AS abbreviation
"""

TIMELINE_COUNT_QUERY = """\
MATCH (t:Timeline)
{where}
RETURN count(t) AS total
"""

TIMELINE_SORT_FIELDS: dict[str, str] = {
    "name": "t.names[0]",
    "start_date": "t.startDate",
    "end_date": "t.endDate",
}
TIMELINE_DEFAULT_SORT = "t.names[0] ASC"

# Item

ITEM_LIST_QUERY = """\
MATCH (i:Item)
{where}
ORDER BY {order_by}
SKIP $skip
LIMIT $limit
RETURN
    i.slug AS slug,
    i.names AS names,
    i.type AS entity_type,
    i.material AS material,
    i.notableFor AS notable_for
"""

ITEM_COUNT_QUERY = """\
MATCH (i:Item)
{where}
RETURN count(i) AS total
"""

ITEM_SORT_FIELDS: dict[str, str] = {
    "name": "i.names[0]",
    "entity_type": "i.type",
    "material": "i.material",
}
ITEM_DEFAULT_SORT = "i.names[0] ASC"

# Language

LANGUAGE_LIST_QUERY = """\
MATCH (lang:Language)
{where}
ORDER BY {order_by}
SKIP $skip
LIMIT $limit
RETURN
    lang.slug AS slug,
    lang.names AS names,
    lang.family AS family
"""

LANGUAGE_COUNT_QUERY = """\
MATCH (lang:Language)
{where}
RETURN count(lang) AS total
"""

LANGUAGE_SORT_FIELDS: dict[str, str] = {
    "name": "lang.names[0]",
    "family": "lang.family",
}
LANGUAGE_DEFAULT_SORT = "lang.names[0] ASC"

# Script

SCRIPT_LIST_QUERY = """\
MATCH (s:Script)
{where}
ORDER BY {order_by}
SKIP $skip
LIMIT $limit
RETURN
    s.slug AS slug,
    s.names AS names
"""

SCRIPT_COUNT_QUERY = """\
MATCH (s:Script)
{where}
RETURN count(s) AS total
"""

SCRIPT_SORT_FIELDS: dict[str, str] = {
    "name": "s.names[0]",
}
SCRIPT_DEFAULT_SORT = "s.names[0] ASC"


CREATE_NODE_TEMPLATE = '''\
CREATE (n:{node_labels} {{slug: $slug, names: $names}})
SET n += $attrs
'''
