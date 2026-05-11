'''
Cypher query constants for the categories app.

Graph schema:
  (:Category {slug, name, createdAt})
  (:Category)-[:SUBCATEGORY_OF]->(:Category)       -- parent-child hierarchy
  (:Page {slug, type, names, imageUrl})-[:IN_CATEGORY]->(:Category)

'''

# List + count

CATEGORY_COUNT_QUERY = '''\
MATCH (c:Category)
WHERE
    ($name IS NULL OR toLower(c.name) CONTAINS toLower($name))
    AND CASE
        WHEN $parent = 'root' THEN NOT exists((c)-[:SUBCATEGORY_OF]->(:Category))
        WHEN $parent IS NOT NULL THEN exists((c)-[:SUBCATEGORY_OF]->(:Category {slug: $parent}))
        ELSE true
    END
RETURN count(c) AS total
'''

CATEGORY_LIST_QUERY = '''\
MATCH (c:Category)
WHERE
    ($name IS NULL OR toLower(c.name) CONTAINS toLower($name))
    AND CASE
        WHEN $parent = 'root' THEN NOT exists((c)-[:SUBCATEGORY_OF]->(:Category))
        WHEN $parent IS NOT NULL THEN exists((c)-[:SUBCATEGORY_OF]->(:Category {slug: $parent}))
        ELSE true
    END
OPTIONAL MATCH (c)<-[:SUBCATEGORY_OF]-(child:Category)
OPTIONAL MATCH (c)<-[:IN_CATEGORY]-(page:Page)
RETURN
    c.slug AS slug,
    c.name AS name,
    toString(c.createdAt) AS created_at,
    coalesce( [(c)-[:SUBCATEGORY_OF]->(p:Category) | p.slug][0], '' ) AS parent_slug,
    count(DISTINCT child) AS child_count,
    count(DISTINCT page) AS page_count
ORDER BY c.slug ASC
SKIP $skip
LIMIT $limit
'''

# Create

CATEGORY_CREATE_QUERY = '''\
CREATE (c:Category {
    slug: $slug,
    name: $name,
    createdAt: datetime()
})
WITH c
OPTIONAL MATCH (parent:Category {slug: $parent_slug})
FOREACH (_ IN CASE WHEN parent IS NOT NULL THEN [1] ELSE [] END |
    CREATE (c)-[:SUBCATEGORY_OF]->(parent)
)
RETURN
    c.slug AS slug,
    c.name AS name,
    toString(c.createdAt) AS created_at,
    coalesce(parent.slug, '') AS parent_slug,
    0 AS child_count,
    0 AS page_count
'''

# Tree

CATEGORY_TREE_QUERY = '''\
MATCH (c:Category)
OPTIONAL MATCH (c)-[:SUBCATEGORY_OF]->(p:Category)
OPTIONAL MATCH (c)<-[:IN_CATEGORY]-(page:Page)
RETURN
    c.slug AS slug,
    c.name AS name,
    p.slug AS parent_slug,
    count(DISTINCT page) AS page_count
ORDER BY c.slug ASC
'''

# Detail info of category

CATEGORY_DETAIL_QUERY = '''\
MATCH (c:Category {slug: $slug})
OPTIONAL MATCH (c)-[:SUBCATEGORY_OF]->(parent:Category)
OPTIONAL MATCH (c)<-[:SUBCATEGORY_OF]-(child:Category)
WITH c, parent, child
OPTIONAL MATCH (child)<-[:IN_CATEGORY]-(child_page:Page)
WITH c, parent, child, count(DISTINCT child_page) AS child_page_count
RETURN
    c.slug AS slug,
    c.name AS name,
    toString(c.createdAt) AS created_at,
    parent.slug AS parent_slug,
    parent.name AS parent_name,
    collect(DISTINCT {
        slug: child.slug,
        name: child.name,
        page_count: child_page_count
    }) AS children
'''

# Count pages in category

CATEGORY_DETAIL_PAGES_COUNT_QUERY = '''\
MATCH (c:Category {slug: $slug})<-[:IN_CATEGORY]-(page:Page)
WHERE ($types IS NULL OR page.type IN $types)
RETURN count(page) AS total
'''

# 

CATEGORY_DETAIL_PAGES_QUERY = '''\
MATCH (c:Category {slug: $slug})<-[:IN_CATEGORY]-(page:Page)
WHERE ($types IS NULL OR page.type IN $types)
RETURN
    page.slug AS slug,
    page.type AS type,
    page.names[0] AS name,
    page.imageUrl AS image_url
ORDER BY page.slug ASC
SKIP $skip
LIMIT $limit
'''

# Update

CATEGORY_UPDATE_QUERY = '''\
MATCH (c:Category {slug: $slug})
SET c.name = $name, c.updatedAt = datetime()
WITH c
OPTIONAL MATCH (c)-[r:SUBCATEGORY_OF]->()
DELETE r
WITH c
OPTIONAL MATCH (newParent:Category {slug: $parent_slug})
FOREACH (_ IN CASE WHEN newParent IS NOT NULL THEN [1] ELSE [] END |
    CREATE (c)-[:SUBCATEGORY_OF]->(newParent)
)
RETURN
    c.slug AS slug,
    c.name AS name,
    toString(c.createdAt) AS created_at,
    newParent.slug AS parent_slug,
    0 AS child_count,
    0 AS page_count
'''

# Delete

CATEGORY_DELETE_QUERY = '''\
MATCH (c:Category {slug: $slug})
DETACH DELETE c
'''

# Check cycle

CYCLE_CHECK_QUERY = '''\
MATCH path = (parent:Category {slug: $parent_slug})-[:SUBCATEGORY_OF*1..]->(child:Category {slug: $slug})
RETURN count(path) > 0 AS would_cycle
'''
