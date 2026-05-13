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
OPTIONAL MATCH (a)-[r]->(b)
WHERE (a:Page OR a:Category OR a:Article)
  AND (b:Page OR b:Category OR b:Article)
WITH nodes, collect(DISTINCT r) AS rels
CALL apoc.export.json.data(nodes, rels, null, {stream: true, useTypes: true})
YIELD data
RETURN data
'''

APOC_IMPORT_QUERY = '''\
CALL apoc.import.json($file_name, {})
YIELD source, format, nodes, relationships, properties, time, rows, batchSize, batches, done, data
RETURN source, format, nodes, relationships, properties, time, rows, batchSize, batches, done, data
'''
