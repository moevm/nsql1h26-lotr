from typing import Any


def rows_to_dicts(rows: list, meta: list) -> list[dict[str, Any]]:
    '''Convert a Cypher result (list of tuples) and column meta to a list of dicts.'''
    return [dict(zip(meta, row)) for row in rows]


def neo4j_dt_to_iso(dt: Any) -> str | None:
    '''Convert a Neo4j DateTime object to an ISO-8601 string, or None.'''
    if dt is None:
        return None
    return dt.isoformat() if hasattr(dt, 'isoformat') else str(dt)
