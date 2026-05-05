from typing import Any

from neomodel import db
from rest_framework.exceptions import ValidationError

from apps.categories.queries import (
    CATEGORY_COUNT_QUERY,
    CATEGORY_CREATE_QUERY,
    CATEGORY_LIST_QUERY,
)
from apps.pages.models import Category


def _neo4j_dt_to_iso(dt: Any) -> str | None:
    """Convert a Neo4j DateTime object to an ISO‑8601 string, or None."""
    if dt is None:
        return None
    if hasattr(dt, 'isoformat'):
        return dt.isoformat()
    return str(dt)


def list_categories(
    page: int,
    page_size: int,
    name: str | None = None,
    parent: str | None = None,
) -> dict[str, Any]:
    """Return paginated list of categories with computed child_count & page_count."""
    skip = (page - 1) * page_size

    count_rows, _ = db.cypher_query(
        CATEGORY_COUNT_QUERY,
        {'name': name, 'parent': parent},
    )
    total = int(count_rows[0][0]) if count_rows else 0

    if total == 0:
        return {
            'count': 0,
            'next': None,
            'previous': None,
            'results': [],
        }

    rows, meta = db.cypher_query(
        CATEGORY_LIST_QUERY,
        {
            'name': name,
            'parent': parent,
            'skip': skip,
            'limit': page_size,
        },
    )
    raw_rows = [dict(zip(meta, row)) for row in rows]

    results = []
    for row in raw_rows:
        results.append({
            'slug': row['slug'],
            'name': row['name'],
            'parent_slug': row['parent_slug'] if row['parent_slug'] else None,
            'child_count': int(row['child_count']),
            'page_count': int(row['page_count']),
            'created_at': _neo4j_dt_to_iso(row.get('created_at')),
        })

    total_pages = max(1, (total + page_size - 1) // page_size)
    next_page = page + 1 if page < total_pages else None
    prev_page = page - 1 if page > 1 else None

    return {
        'count': total,
        'next': next_page,
        'previous': prev_page,
        'results': results,
    }


def create_category(
    slug: str | None,
    name: str,
    parent_slug: str | None = None,
) -> dict[str, Any]:
    """Create a new category. Returns the created category data."""
    name = name.strip()
    if not name:
        raise ValidationError({'name': ['Name must not be empty.']})

    if not slug:
        from django.utils.text import slugify
        slug = slugify(name)
        if not slug:
            raise ValidationError({'slug': ['Could not generate a valid slug from the name.']})

    if Category.nodes.filter(slug=slug).exists():
        raise ValidationError({'slug': ['Category with this slug already exists.']})

    rows, meta = db.cypher_query(
        CATEGORY_CREATE_QUERY,
        {
            'slug': slug,
            'name': name,
            'parent_slug': parent_slug or None,
        },
    )
    raw = dict(zip(meta, rows[0]))

    return {
        'slug': raw['slug'],
        'name': raw['name'],
        'parent_slug': raw['parent_slug'] or None,
        'child_count': int(raw['child_count']),
        'page_count': int(raw['page_count']),
        'created_at': _neo4j_dt_to_iso(raw.get('created_at')),
    }