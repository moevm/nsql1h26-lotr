from typing import Any

from neo4j.exceptions import ClientError
from neomodel import db  # type: ignore[attr-defined]
from rest_framework.exceptions import ValidationError

from .queries import (
    SEARCH_QUERY,
    VALID_TYPES,
    TYPE_TO_LABEL,
    build_lucene_query,
    labels_to_type,
)


def _parse_types(raw_types: str) -> list[str] | None:
    '''
    Parse and validate the `types` query parameter.
    '''
    if not raw_types or not raw_types.strip():
        return None

    requested: list[str] = [
        t.strip() for t in raw_types.split(',') if t.strip()
    ]
    if not requested:
        return None

    invalid = sorted(set(requested) - VALID_TYPES)
    if invalid:
        raise ValidationError(
            {
                'types': [
                    f'Invalid type(s): {", ".join(invalid)}. '
                    f'Allowed: {", ".join(sorted(VALID_TYPES))}'
                ]
            }
        )

    return [TYPE_TO_LABEL[t] for t in requested]


def _row_to_result(row: dict[str, Any]) -> dict[str, Any]:
    '''Convert one raw query result row to the search result summary dict'''
    names: list[str] = row.get('names') or []

    return {
        'slug': row['slug'],
        'type': labels_to_type(row.get('node_labels') or []) or 'unknown',
        'name': names[0] if names else None,
        'names': names,
        'image_url': row.get('image_url')
    }


def search(
        q: str,
        raw_types: str,
        limit: int,
) -> list[dict[str, Any]]:
    '''
    Run a fulltext search across all :Page nodes
    '''
    type_labels = _parse_types(raw_types)
    lucene_query = build_lucene_query(q)

    try:
        results, meta = db.cypher_query(
            SEARCH_QUERY,
            {
                'query': lucene_query,
                'type_labels': type_labels,
                'limit': limit,
            },
        )
    except ClientError as exc:
        if "There is no such fulltext schema index" in str(exc):
            from rest_framework.exceptions import APIException
            raise APIException(
                detail="Search index is not available.",
                code="SEARCH_INDEX_UNAVAILABLE",
            )
        raise

    return [_row_to_result(dict(zip(meta, row))) for row in results]
