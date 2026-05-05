'''
Internal utility helpers
'''

from typing import Any


def rows_to_dicts(rows: list, meta: list[str]) -> list[dict[str, Any]]:
    return [dict(zip(meta, row, strict=True)) for row in rows]


def entity_type_from_labels(labels: list[str]) -> str:
    for label in labels:
        if label != 'Page':
            return label.lower()

    return 'unknown'
