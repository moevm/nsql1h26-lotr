'''
Cypher query constants for the comments app.

Graph schema:
  (:User {django_id})-[:WROTE]->(:Comment {elementId, text, createdAt, updatedAt})-[:ON]->(:Page {slug})

Design notes:
    - Comment ID exposed to the client is elementId().
    - Author info is joined from :User via [:WROTE] → Django User table (username / avatar_url)
    must be fetched separately in Python, since Neo4j :User only stores django_id.
    - MERGE on UserRef (django_id) before WROTE ensures the Neo4j :User node exists
    idempotently without a dedicated 'create user' endpoint, matching the same
    pattern used by PAGE_LIKE_ADD_QUERY in pages/queries.py.
'''


# List + count

COMMENT_LIST_QUERY = '''\
MATCH (c:Comment)-[:ON]->(p:Page {slug: $slug})
MATCH (u:User)-[:WROTE]->(c)
RETURN
    elementId(c) AS id,
    c.text AS text,
    u.django_id AS author_django_id,
    c.createdAt AS created_at,
    c.updatedAt AS updated_at
ORDER BY c.createdAt DESC
SKIP $skip
LIMIT $limit
'''

COMMENT_COUNT_QUERY = '''\
MATCH (c:Comment)-[:ON]->(p:Page {slug: $slug})
RETURN count(c) AS total
'''


# Create

COMMENT_CREATE_QUERY = '''\
MATCH (p:Page {slug: $slug})
MERGE (u:User {django_id: $django_id})
CREATE (c:Comment {text: $text, createdAt: datetime(), updatedAt: datetime()})
CREATE (u)-[:WROTE]->(c)
CREATE (c)-[:ON]->(p)
RETURN
    elementId(c) AS id,
    c.text AS text,
    u.django_id AS author_django_id,
    c.createdAt AS created_at,
    c.updatedAt AS updated_at
'''


# Delete

# Returns the author's django_id so the service can check ownership
# before deleting. One round-trip instead of two.
COMMENT_FETCH_AUTHOR_QUERY = '''\
MATCH (u:User)-[:WROTE]->(c:Comment)-[:ON]->(p:Page {slug: $slug})
WHERE elementId(c) = $comment_id
RETURN u.django_id AS author_django_id
'''

COMMENT_DELETE_QUERY = '''\
MATCH (c:Comment)-[:ON]->(p:Page {slug: $slug})
WHERE elementId(c) = $comment_id
DETACH DELETE c
'''


# Update

COMMENT_UPDATE_QUERY = '''\
MATCH (u:User)-[:WROTE]->(c:Comment)-[:ON]->(p:Page {slug: $slug})
WHERE elementId(c) = $comment_id
SET c.text = $text, c.updatedAt = datetime()
RETURN
    elementId(c) AS id,
    c.text AS text,
    u.django_id AS author_django_id,
    c.createdAt AS created_at,
    c.updatedAt AS updated_at
'''


# Page exsitence check (pre-flight guard)
PAGE_EXISTS_QUERY = '''\
MATCH (p:Page {slug: $slug})
RETURN p.slug AS slug
'''