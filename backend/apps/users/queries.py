'''
Neo4j queries for the users app.

Node/relationship schema relevant here:
  (:User {django_id}) - mirrors the Django User (created on first interaction)
  (u:User)-[:WROTE]->(c:Comment)
  (u:User)-[:LIKED]->(p:Page)
  (p:Page)-[:HAS_ARTICLE]->(a:Article
'''


# Returns N rows (up to 11 - 10 liked pages + 1 possible null-row when there
# are no likes).
# All rows share the same comments_count / liked_pages_total.
# A row with slug=null means "no liked pages" - handled in the service.
GET_USER_NEO4J_STATS_QUERY = '''\
MATCH (u:User {django_id: $django_id})
OPTIONAL MATCH (u)-[:WROTE]->(c:Comment)
OPTIONAL MATCH (u)-[:LIKED]->(p:Page)
WITH count(DISTINCT c) AS comments_count,
    count(DISTINCT p) AS liked_pages_total,
    collect(DISTINCT p)[..10] AS top_pages
UNWIND CASE WHEN size(top_pages) > 0 THEN top_pages ELSE [null] END AS page_node
OPTIONAL MATCH (page_node)-[:HAS_ARTICLE]->(a:Article)
RETURN
    comments_count,
    liked_pages_total,
    page_node.slug AS slug,
    labels(page_node) AS node_labels,
    page_node.names[0] AS name,
    a.imageUrl AS image_url

'''


# Done as COUNT + LIST query pair as in other apps.
GET_LIKED_PAGES_COUNT_QUERY = '''\
MATCH (u:User {django_id: $django_id})-[:LIKED]->(p:Page)
RETURN count(p) AS total
'''

GET_LIKED_PAGES_PAGINATED_QUERY = '''\
MATCH (u:User {django_id: $django_id})-[:LIKED]->(p:Page)
OPTIONAL MATCH (p)-[:HAS_ARTICLE]->(a:Article)
RETURN
    p.slug AS slug,
    labels(p) AS node_labels,
    p.names[0] AS name,
    a.imageUrl AS image_url
ORDER BY p.names[0] ASC
SKIP $skip
LIMIT $limit
'''


# OPTIONAL MATCH + DETACH DELETE null is safe in Cypher.
# This handles users who never interacted with the graph.
DELETE_USER_NEO4J_QUERY = '''\
OPTIONAL MATCH (u:User {django_id: $django_id})
OPTIONAL MATCH (u)-[:WROTE]->(c:Comment)
DETACH DELETE u, c
'''
