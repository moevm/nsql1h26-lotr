'''
Cypher constants and query-building utilities for the search app.

Index name: page_names_fulltext
Labeled on: :Page
Property: names  (LIST<STRING>)
Analyzer: standard-no-stop-words (default)

Query building - Lucene prefix query
The endpoint is for autocomplete (navbar search, analytics entity picker).
Users type prefixes; we want prefix matching ('frod' → 'Frodo Baggins').

Security: \\w+ extraction guarantees that Lucene special characters
(+ - ! && || ( ) { } [ ] ^ ' ~ * ? : \\ /) cannot survive the sanitisation
step.
'''

import re

from apps.pages.queries import LABEL_TO_TYPE, labels_to_type

__all__ = [
    'FULLTEXT_INDEX_NAME',
    'ENSURE_FULLTEXT_INDEX_QUERY',
    'SEARCH_QUERY',
    'VALID_TYPES',
    'TYPE_TO_LABEL',
    'labels_to_type',
    'build_lucene_query',
]


# Type metadata

TYPE_TO_LABEL: dict[str, str] = {v: k for k, v in LABEL_TO_TYPE.items()}

VALID_TYPES: frozenset[str] = frozenset(TYPE_TO_LABEL.keys())


# Index management

FULLTEXT_INDEX_NAME = 'page_names_default'

# Idempotent fulltext index creation
ENSURE_FULLTEXT_INDEX_QUERY = f'''
CREATE FULLTEXT INDEX {FULLTEXT_INDEX_NAME} IF NOT EXISTS
FOR (p:Page) ON EACH [p.names]
'''


# Search query

# Fulltext search across all :Page nodes.
# Parameters:
#   $query - Lucene query string built by build_lucene_query()
#   $type_labels - list[str] of Neo4j labels to filter to or null for all types
#   $limit - max results to return (int)
SEARCH_QUERY = f'''
CALL db.index.fulltext.queryNodes('{FULLTEXT_INDEX_NAME}', $query)
YIELD node, score
WHERE ($type_labels IS NULL OR ANY(lbl IN labels(node) WHERE lbl IN $type_labels))
WITH node, score
ORDER BY score DESC
LIMIT $limit
OPTIONAL MATCH (node)-[:HAS_ARTICLE]->(a:Article)
RETURN
    node.slug AS slug,
    labels(node) AS node_labels,
    node.names AS names,
    a.imageUrl AS image_url
'''


# Lucene query builder

_WORD_RE = re.compile(r'\w+', re.UNICODE)


def build_lucene_query(raw: str) -> str:
    '''Sanitise user input and produce a safe Lucene prefix query.'''
    tokens = _WORD_RE.findall(raw.lower())
    if not tokens:
        return '""'

    # Boost main name
    # clauses = []
    # for token in tokens:
    #     clauses.append(f'(names[0]:{token}*)^2 OR names:{token}*')

    return " AND ".join(f'{token}*' for token in tokens)
