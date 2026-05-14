'''
Business logic for bulk export / import.
'''

import json
import os
import uuid
from datetime import date

from django.core.cache import cache
from django.http import HttpResponse
from rest_framework.exceptions import ValidationError

from .repository import BulkRepository

repo = BulkRepository()
SHARED_DIR = '/shared'


def bulk_export() -> HttpResponse:
    '''Stream all lore data as a downloadable JSON attachment.'''
    json_data = repo.export_lore_data()

    if not json_data:
        json_data = '{}'

    filename = f'lotr-wiki-export-{date.today()}.json'
    return HttpResponse(
        json_data,
        content_type='application/json',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"',
        },
    )


def bulk_import(uploaded_file) -> dict:
    if not uploaded_file:
        raise ValidationError({
            'file': ['No file provided.']
        })

    content = uploaded_file.read()
    if not content or not content.strip():
        raise ValidationError(
            {"file": ["File is empty."]},
            code="INVALID_FORMAT",
        )
    first_line = content.split(b"\n", 1)[0].strip()
    try:
        json.loads(first_line)
    except json.JSONDecodeError as exc:
        raise ValidationError(
            {"file": [f"Invalid format - first line is not valid JSON: {exc}"]},
            code='INVALID_FORMAT',
        ) from exc

    temp_filename = f'import_{uuid.uuid4().hex}.json'
    temp_path = os.path.join(SHARED_DIR, temp_filename)
    apoc_file_path = f'shared/{temp_filename}'

    with open(temp_path, 'wb+') as dest:
        dest.write(content)

    try:
        repo.ensure_import_constraints()

        repo.clear_lore_data()

        stats = repo.import_from_file(apoc_file_path)

        cache.delete('analytics:global')

        return _format_import_result(stats)

    except Exception:
        raise
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def _format_import_result(stats: dict) -> dict:
    '''Shape the APOC import stats into the API response format.'''
    return {
        'imported': {
            'nodes': stats.get('nodes', 0),
            'relationships': stats.get('relationships', 0),
        },
        'skipped': 0,
        'errors': [],
    }
