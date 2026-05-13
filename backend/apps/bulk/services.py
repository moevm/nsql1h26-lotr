"""
Business logic for bulk export/import.
"""

import os
import uuid

from django.http import HttpResponse
from rest_framework.exceptions import ValidationError

from apps.bulk.repository import BulkRepository

repo = BulkRepository()
SHARED_DIR = '/shared'


def bulk_export() -> HttpResponse:
    stats = repo.export_lore_data()
    file_content = stats.get('data', '')

    return HttpResponse(
        file_content,
        content_type='application/json',
        headers={
            'Content-Disposition': 'attachment; filename="lotr-wiki-export.json"',
        },
    )


def bulk_import(file) -> dict:
    if not file:
        raise ValidationError({'file': 'No file provided.'})

    temp_filename = f'import_{uuid.uuid4().hex}.json'
    temp_path = os.path.join(SHARED_DIR, temp_filename)
    apoc_file_path = f'shared_data/{temp_filename}'

    with open(temp_path, 'wb+') as dest:
        for chunk in file.chunks():
            dest.write(chunk)

    try:
        repo.clear_lore_data()
        stats = repo.import_from_shared_file(apoc_file_path)

        return {
            'imported': {
                'nodes': stats.get('nodes', 0),
                'relationships': stats.get('relationships', 0),
            },
            'skipped': 0,
            'errors': [],
        }
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
