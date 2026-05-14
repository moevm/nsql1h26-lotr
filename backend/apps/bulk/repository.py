'''
Repository layer for bulk operations.
'''


from neomodel import db

from .queries import (
    APOC_EXPORT_QUERY,
    APOC_IMPORT_QUERY,
    CLEAR_LORE_DATA_QUERY,
    CONSTRAINT_LABELS,
)


class BulkRepository:

    def clear_lore_data(self) -> None:
        db.cypher_query(CLEAR_LORE_DATA_QUERY)

    def ensure_import_constraints(self) -> None:
        for label in CONSTRAINT_LABELS:
            db.cypher_query(
                f'CREATE CONSTRAINT IF NOT EXISTS '
                f'FOR (n:{label}) REQUIRE n.neo4jImportId IS UNIQUE'
            )

    def drop_import_constraints(self) -> None:
        for label in CONSTRAINT_LABELS:
            db.cypher_query(
                f'DROP CONSTRAINT IF EXISTS '
                f'FOR (n:{label}) REQUIRE n.neo4jImportId IS UNIQUE'
            )

    def export_lore_data(self) -> str:
        rows, meta = db.cypher_query(APOC_EXPORT_QUERY)
        if not rows:
            return ''

        data_idx = list(meta).index('data')
        chunks = [row[data_idx] for row in rows if row[data_idx] is not None]
        return ''.join(chunks)

    def import_from_file(self, file_name: str) -> dict:
        rows, meta = db.cypher_query(
            APOC_IMPORT_QUERY,
            {'file_name': file_name},
        )
        if not rows:
            return {}
        return dict(zip(meta, rows[0]))
