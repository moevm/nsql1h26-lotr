"""
Repository layer for bulk operations.
"""

from neomodel import db

from .queries import (
    APOC_EXPORT_QUERY,
    APOC_IMPORT_QUERY,
    CLEAR_LORE_DATA_QUERY,
)


class BulkRepository:
    def clear_lore_data(self) -> None:
        db.cypher_query(CLEAR_LORE_DATA_QUERY, {})

    def export_lore_data(self) -> dict:
        rows, meta = db.cypher_query(APOC_EXPORT_QUERY, {})
        return dict(zip(meta, rows[0])) if rows else {}

    def import_from_shared_file(self, file_name: str) -> dict:
        rows, meta = db.cypher_query(
            APOC_IMPORT_QUERY,
            {'file_name': file_name}
        )
        return dict(zip(meta, rows[0])) if rows else {}
