"""
Business logic for category endpoints.
"""

from typing import Any

from django.utils.text import slugify
from neomodel import db
from rest_framework.exceptions import NotFound, ValidationError

from apps.categories.queries import (
    CATEGORY_COUNT_QUERY,
    CATEGORY_CREATE_QUERY,
    CATEGORY_DELETE_QUERY,
    CATEGORY_DETAIL_PAGES_COUNT_QUERY,
    CATEGORY_DETAIL_PAGES_QUERY,
    CATEGORY_DETAIL_QUERY,
    CATEGORY_LIST_QUERY,
    CATEGORY_TREE_QUERY,
    CATEGORY_UPDATE_QUERY,
    CYCLE_CHECK_QUERY,
)
from apps.pages.models import Category


def _neo4j_dt_to_iso(dt: Any) -> str | None:
    '''Convert a Neo4j DateTime object to an ISO-8601 string, or None'''
    if dt is None:
        return None

    if hasattr(dt, 'isoformat'):
        return dt.isoformat()

    return str(dt)


def _validate_sort(sort: str | None) -> str:
    allowed = ['name']
    if sort and sort not in allowed:
        raise ValidationError({'sort': f'Sort must be one of: {", ".join(allowed)}.'})
    return sort or 'name'


def _check_cycle(slug: str, new_parent: str) -> None:
    if new_parent == slug:
        raise ValidationError({'parent_slug': ['A category cannot be its own parent.']})
    rows, _ = db.cypher_query(
        CYCLE_CHECK_QUERY,
        {'slug': slug, 'parent_slug': new_parent},
    )
    if rows and rows[0][0]:
        raise ValidationError(
            {'parent_slug': ['This would create a cycle in the category tree.']}
        )


def list_categories(
    page: int,
    page_size: int,
    name: str | None = None,
    parent: str | None = None,
) -> dict[str, Any]:
    skip = (page - 1) * page_size
    count_rows, _ = db.cypher_query(
        CATEGORY_COUNT_QUERY, {'name': name, 'parent': parent}
    )
    total = int(count_rows[0][0]) if count_rows else 0

    if total == 0:
        return {'count': 0, 'next': None, 'previous': None, 'results': []}

    rows, meta = db.cypher_query(
        CATEGORY_LIST_QUERY,
        {'name': name, 'parent': parent, 'skip': skip, 'limit': page_size},
    )
    raw_rows = [dict(zip(meta, row)) for row in rows]

    results = []
    for row in raw_rows:
        results.append(
            {
                'slug': row['slug'],
                'name': row['name'],
                'parent_slug': row['parent_slug'] or None,
                'child_count': int(row['child_count']),
                'page_count': int(row['page_count']),
                'created_at': _neo4j_dt_to_iso(row.get('created_at')),
            }
        )

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
    name = name.strip()
    if not name:
        raise ValidationError({'name': ['Name must not be empty.']})

    if not slug:
        slug = slugify(name)
        if not slug:
            raise ValidationError({'slug': ['Couldnt generate valid slug from name.']})

    if Category.nodes.filter(slug=slug).exists():
        raise ValidationError({'slug': ['Category with this slug already exists.']})

    effective_parent = parent_slug.strip() if parent_slug else None
    if effective_parent:
        if effective_parent == slug:
            raise ValidationError(
                {'parent_slug': ['A category cannot be its own parent.']},
                code='CYCLE_DETECTED',
            )
        if not Category.nodes.filter(slug=effective_parent).exists():
            raise NotFound(
                f"Parent category '{effective_parent}' does not exist.",
                code='NOT_FOUND',
            )

    rows, meta = db.cypher_query(
        CATEGORY_CREATE_QUERY,
        {
            'slug': slug,
            'name': name,
            'parent_slug': effective_parent or None,
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


def get_category_tree(root: str | None = None) -> list[dict[str, Any]]:
    """
    Return full category tree, optionally rooted at `root`.
    Builds tree from a flat list of categories with parent_slug.
    """
    rows, meta = db.cypher_query(CATEGORY_TREE_QUERY, {})
    all_cats = [dict(zip(meta, row)) for row in rows]

    slug_to_node: dict[str, dict] = {}
    for cat in all_cats:
        slug_to_node[cat['slug']] = {
            'slug': cat['slug'],
            'name': cat['name'],
            'page_count': int(cat['page_count']),
            'children': [],
        }

    roots = []
    for cat in all_cats:
        node = slug_to_node[cat['slug']]
        parent = cat['parent_slug']
        if parent and parent in slug_to_node:
            slug_to_node[parent]['children'].append(node)
        else:
            roots.append(node)

    if root:
        def find_subtree(slug: str):
            if slug in slug_to_node:
                return slug_to_node[slug]
            raise NotFound(f"Category '{slug}' not found.")

        return [find_subtree(root)]

    return roots


def get_category_detail(
    slug: str,
    page: int,
    page_size: int,
    types: str | None = None,
    sort: str | None = None,
) -> dict[str, Any]:
    _validate_sort(sort)

    rows, meta = db.cypher_query(CATEGORY_DETAIL_QUERY, {'slug': slug})
    if not rows:
        raise NotFound(f"Category '{slug}' does not exist.")
    raw = dict(zip(meta, rows[0]))

    parent = None
    if raw['parent_slug']:
        parent = {
            'slug': raw['parent_slug'],
            'name': raw['parent_name'],
        }

    children = []
    if raw['children']:
        for child in raw['children']:
            children.append(
                {
                    'slug': child['slug'],
                    'name': child['name'],
                    'page_count': int(child['page_count']),
                }
            )

    type_list = None
    if types:
        type_list = [t.strip() for t in types.split(',') if t.strip()]

    count_rows, _ = db.cypher_query(
        CATEGORY_DETAIL_PAGES_COUNT_QUERY,
        {'slug': slug, 'types': type_list},
    )
    total_pages_count = int(count_rows[0][0]) if count_rows else 0

    skip = (page - 1) * page_size
    pages_rows, pages_meta = db.cypher_query(
        CATEGORY_DETAIL_PAGES_QUERY,
        {
            'slug': slug,
            'types': type_list,
            'skip': skip,
            'limit': page_size,
        },
    )
    page_items = []
    for prow in pages_rows:
        rec = dict(zip(pages_meta, prow))
        page_items.append(
            {
                'slug': rec['slug'],
                'type': rec['type'],
                'name': rec['name'],
                'image_url': rec.get('image_url'),
            }
        )

    total_pages = max(1, (total_pages_count + page_size - 1) // page_size)
    next_page = page + 1 if page < total_pages else None
    prev_page = page - 1 if page > 1 else None

    return {
        'slug': raw['slug'],
        'name': raw['name'],
        'created_at': _neo4j_dt_to_iso(raw.get('created_at')),
        'parent_slug': raw['parent_slug'],
        'parent': parent,
        'children': children,
        'pages': {
            'count': total_pages_count,
            'next': next_page,
            'previous': prev_page,
            'results': page_items,
        },
    }


def update_category(
    slug: str,
    name: str | None = None,
    parent_slug: str | None = None,
) -> dict[str, Any]:
    if not Category.nodes.filter(slug=slug).exists():
        raise NotFound(f"Category '{slug}' does not exist.")

    if name is not None:
        name = name.strip()
        if not name:
            raise ValidationError({'name': ['Name must not be empty.']})
    else:
        name = Category.nodes.get(slug=slug).name

    if parent_slug is not None and parent_slug != slug:
        _check_cycle(slug, parent_slug)

    rows, meta = db.cypher_query(
        CATEGORY_UPDATE_QUERY,
        {'slug': slug, 'name': name, 'parent_slug': parent_slug or None},
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


def delete_category(slug: str) -> None:
    if not Category.nodes.filter(slug=slug).exists():
        raise NotFound(f"Category '{slug}' does not exist.")
    db.cypher_query(CATEGORY_DELETE_QUERY, {'slug': slug})
