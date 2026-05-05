CATEGORY_COUNT_QUERY = '''\
MATCH (c:Category)
WHERE
    ($name IS NULL OR toLower(c.name) CONTAINS toLower($name))
    AND CASE
        WHEN $parent = 'root' THEN NOT exists((c)-[:SUBCATEGORY_OF]->(:Category))
        WHEN $parent IS NOT NULL THEN exists((c)-[:SUBCATEGORY_OF]->(parent:Category {slug: $parent}))
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
        WHEN $parent IS NOT NULL THEN exists((c)-[:SUBCATEGORY_OF]->(parent:Category {slug: $parent}))
        ELSE true
    END
OPTIONAL MATCH (c)<-[:SUBCATEGORY_OF]-(child:Category)
OPTIONAL MATCH (c)<-[:IN_CATEGORY]-(page:Page)
RETURN
    c.slug AS slug,
    c.name AS name,
    c.createdAt AS created_at,
    // parent slug (empty string if root)
    coalesce( [(c)-[:SUBCATEGORY_OF]->(p:Category) | p.slug][0], '' ) AS parent_slug,
    count(DISTINCT child) AS child_count,
    count(DISTINCT page) AS page_count
ORDER BY c.slug ASC
SKIP $skip
LIMIT $limit
'''

CATEGORY_CREATE_QUERY = '''\
CREATE (c:Category {
    slug: $slug,
    name: $name,
    createdAt: datetime()
})
WITH c
// If parent_slug is provided attach to parent
OPTIONAL MATCH (parent:Category {slug: $parent_slug})
FOREACH (_ IN CASE WHEN parent IS NOT NULL THEN [1] ELSE [] END |
    CREATE (c)-[:SUBCATEGORY_OF]->(parent)
)
RETURN
    c.slug AS slug,
    c.name AS name,
    c.createdAt AS created_at,
    coalesce(parent.slug, '') AS parent_slug,
    0 AS child_count,
    0 AS page_count
'''