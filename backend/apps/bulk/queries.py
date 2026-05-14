"""
Cypher query constants for the bulk import/export app.
"""

CLEAR_LORE_DATA_QUERY = '''\
MATCH (n)
WHERE n:Page OR n:Category OR n:Article
DETACH DELETE n
'''


APOC_EXPORT_QUERY = '''\
MATCH (n)
WHERE n:Page OR n:Category OR n:Article
WITH collect(DISTINCT n) AS nodes
UNWIND nodes AS src
OPTIONAL MATCH (src)-[r]->(dst)
WHERE dst:Page OR dst:Category OR dst:Article
WITH nodes, collect(DISTINCT r) AS raw_rels
WITH nodes, [rel IN raw_rels WHERE rel IS NOT NULL] AS rels
CALL apoc.export.json.data(nodes, rels, null, {stream: true})
YIELD data
RETURN data
'''

APOC_IMPORT_QUERY = '''\
CALL apoc.import.json($file_name, {})
YIELD source, format, nodes, relationships, properties, time, rows, batchSize, batches, done, data
RETURN source, format, nodes, relationships, properties, time, rows, batchSize, batches, done, data
'''

CONSTRAINT_LABELS: list[str] = [
    "Page",
    "Character",
    "Race",
    "Location",
    "Event",
    "Organization",
    "Timeline",
    "Item",
    "Language",
    "Script",
    "Category",
    "Article",
]
