'''
Creates all custom Neo4j indexes that cannot be expressed through neomodel's
declarative model syntax (neomodel only supports basic range indexes).

Currently manages:
    - page_names_fulltext: FULLTEXT index on Page.names for global search.

Idempotent by design (uses IF NOT EXISTS), safe to run on every container
start.
Called from entrypoint.sh after neomodel_install_labels.

Usage: python manage.py ensure_indexes
'''

from django.core.management.base import BaseCommand
from neomodel import db  # type: ignore[attr-defined]

from apps.search.queries import (
    ENSURE_FULLTEXT_INDEX_QUERY,
    FULLTEXT_INDEX_NAME,
)


class Command(BaseCommand):
    help = ('Create custom Neo4j indexes (fulltext, etc.) '
            'that neomodel cannot manage.')

    def handle(self, *args, **kwargs) -> None:
        self.stdout.write(f'Ensuring Neo4j index: {FULLTEXT_INDEX_NAME} ...')

        try:
            db.cypher_query(ENSURE_FULLTEXT_INDEX_QUERY)
        except Exception as exc:  # noqa: BLE001
            self.stderr.write(
                self.style.ERROR(
                    f'Failed to create fulltext index '
                    f'\'{FULLTEXT_INDEX_NAME}\': {exc}'
                )
            )
            raise SystemExit(1) from exc

        self.stdout.write(
            self.style.SUCCESS(
                f'Index \'{FULLTEXT_INDEX_NAME}\' is ready'
            )
        )
