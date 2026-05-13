"""
Cypher query constants for the bulk import/export app.
"""

CLEAR_LORE_DATA_QUERY = '''\
MATCH (n)
WHERE n:Page OR n:Category OR n:Article
DETACH DELETE n
'''

APOC_EXPORT_QUERY = '''\
CALL apoc.export.json.all('/shared/export.json', {
    writeNodeProperties: true,
    excludeLabels: ['User', 'Comment'],
    excludeRels: ['LIKED', 'WROTE', 'ON', 'REPLY_TO']
})
YIELD file, nodes, relationships, properties, time
RETURN file, nodes, relationships, properties, time
'''

APOC_IMPORT_QUERY = '''\
CALL apoc.import.json($file_path)
YIELD source, format, nodes, relationships, properties, time
RETURN source, format, nodes, relationships, properties, time
'''
