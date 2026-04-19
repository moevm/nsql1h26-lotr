from typing import Any

from neomodel import db  # type: ignore[attr-defined]


def get_liked_pages(user_id: int) -> list[dict[str, Any]]:
    '''
    Returns pages liked by the user (Neo4j).
    Keeps serializers SQL-only.
    '''

    query = """\
    MATCH (u:User {django_id: $user_id})-[:LIKED]->(p:Page)
    RETURN p.slug AS slug, p.names[0] AS name
    ORDER BY p.names[0]
    """
    results, _ = db.cypher_query(query, {'user_id': user_id})

    if not results:
        return []

    return [{'slug': row[0], 'name': row[1]} for row in results]
