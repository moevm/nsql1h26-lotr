'''
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
'''
from apps.pages.enums import EntityType, SocRelTypes

from .constants import MOST_COMMENTED_LIMIT, MOST_LIKED_LIMIT

# Counts

# RETURN
#     count(p) AS total,
#     count(p:Character) AS characters,
#     count(p:Race) AS races,
#     ...
# does not work for some reason - always returns {total, total, total, ...}.
# May be a quirk of Neo4j??
COUNTS_QUERY = '''\
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
'''


# Entity by property

CHARACTERS_BY_RACE_QUERY = '''\
MATCH (c:Character)-[:OF_RACE]->(r:Race)
RETURN
    r.slug AS slug,
    r.names[0] AS name,
    count(c) AS count
ORDER BY count DESC, name ASC
'''

CHARACTERS_BY_GENDER_QUERY = '''\
MATCH (c:Character)
RETURN
    coalesce(c.gender, 'unknown') AS gender,
    count(c) AS count
ORDER BY count DESC
'''

CHARACTERS_BY_IS_ALIVE_COUNT_QUERY = '''\
MATCH (c:Character)
RETURN
    count(CASE WHEN c.deathDate IS NULL THEN 1 END) AS alive,
    count(CASE WHEN c.deathDate IS NOT NULL THEN 1 END) AS deceased
'''

EVENTS_BY_TIMELINE_QUERY = '''\
MATCH (e:Event)-[:OCCURRED_DURING]->(t:Timeline)
WITH t, count(e) AS event_count
ORDER BY event_count DESC
RETURN
    t.slug AS timeline_slug,
    t.names[0] AS name,
    event_count AS count
'''

LOCATIONS_BY_TYPE_QUERY = '''\
MATCH (l:Location)
WHERE l.type IS NOT NULL
RETURN l.type AS type, count(l) AS count
ORDER BY count DESC
'''

ITEMS_BY_TYPE_QUERY = '''\
MATCH (i:Item)
WHERE i.type IS NOT NULL
RETURN i.type AS type, count(i) AS count
ORDER BY count DESC
'''

# Top connected

_TOP_CONNECTED_TEMPLATE = '''\
MATCH (n:{label})
WITH n,
     size([(n)-[r]-() WHERE NOT type(r) IN {excluded} | r]) AS connections
ORDER BY connections DESC, n.names[0] ASC
LIMIT 5
RETURN n.slug AS slug, n.names[0] AS name, connections AS connections_count
'''

def top_connected_query(label: str) -> str:
    '''Build a top-connected query for the given :Page sub-label.'''
    return _TOP_CONNECTED_TEMPLATE.format(
        label=label,
        excluded=f'[{', '.join('\'' + str(x) + '\'' for x in SocRelTypes)}]',
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

MOST_LIKED_QUERY = f'''\
MATCH (:User)-[:LIKED]->(p:Page)
WITH p, count(*) AS likes_count
ORDER BY likes_count DESC
LIMIT {MOST_LIKED_LIMIT}
RETURN
    p.slug AS slug,
    p.names[0] AS name,
    labels(p) AS lbls,
    likes_count AS count
'''

MOST_COMMENTED_QUERY = f'''\
MATCH (c:Comment)-[:ON]->(p:Page)
WITH p, count(c) AS comment_count
ORDER BY comment_count DESC
LIMIT {MOST_COMMENTED_LIMIT}
RETURN
    p.slug AS slug,
    p.names[0] AS name,
    labels(p) AS lbls,
    comment_count AS count
'''