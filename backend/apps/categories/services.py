"""
Business logic for category endpoints.
"""

from typing import Any

from django.utils.text import slugify
from rest_framework.exceptions import NotFound, ValidationError

from apps.catalogs.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from apps.categories.repository import (
    CategoryRepositoryProtocol,
    Neo4jCategoryRepository,
)

_default_repo = Neo4jCategoryRepository()


def _parse_int(value: str | None, default: int) -> int:
    '''Parse a query-param string to an integer, returning default on error.'''
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def _validate_sort(sort: str | None) -> str:
    '''Whitelist sort field for categories endpoints.'''
    allowed = ['name', 'slug']
    if sort and sort not in allowed:
        raise ValidationError({
            'sort': f'Sort must be one of: {", ".join(allowed)}.'
        })
    return sort or 'slug'


def _check_cycle(slug: str, new_parent: str,
                 repo: CategoryRepositoryProtocol) -> None:
    if new_parent == slug:
        raise ValidationError(
            {'parent_slug': ['A category cannot be its own parent.']},
            code='CYCLE_DETECTED',
        )
    if repo.would_create_cycle(slug, new_parent):
        raise ValidationError(
            {'parent_slug': ['This would create a cycle in the category tree.']},
            code='CYCLE_DETECTED',
        )


def list_categories(
    raw_page: str | None = None,
    raw_page_size: str | None = None,
    raw_name: str | None = None,
    raw_parent: str | None = None,
    raw_sort: str | None = None,
    raw_order: str | None = None,
    *,
    repo: CategoryRepositoryProtocol = _default_repo,
) -> dict[str, Any]:
    page = max(1, _parse_int(raw_page, 1))
    page_size = min(
        MAX_PAGE_SIZE,
        max(1, _parse_int(raw_page_size, DEFAULT_PAGE_SIZE)),
    )
    skip = (page - 1) * page_size

    name = raw_name.strip() if raw_name else None
    parent = raw_parent.strip() if raw_parent else None
    sort_field = _validate_sort(raw_sort)
    order = (raw_order or 'asc').strip().lower()
    if order not in ('asc', 'desc'):
        order = 'asc'

    total = repo.count_categories(name=name, parent=parent)
    if total == 0:
        return {
            'count': 0,
            'next': None,
            'previous': None,
            'results': [],
        }

    rows = repo.list_categories(
        name=name,
        parent=parent,
        skip=skip,
        limit=page_size,
        sort=sort_field,
        order=order,
    )

    results = [
        {
            'slug': r.slug,
            'name': r.name,
            'parent_slug': r.parent_slug,
            'child_count': r.child_count,
            'page_count': r.page_count,
            'created_at': r.created_at,
        }
        for r in rows
    ]

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
    *,
    repo: CategoryRepositoryProtocol = _default_repo,
) -> dict[str, Any]:
    name = name.strip()
    if not name:
        raise ValidationError({'name': ['Name must not be empty.']})

    if not slug:
        slug = slugify(name)
        if not slug:
            raise ValidationError(
                {'slug': ['Could not generate a valid slug from the name.']}
                )

    if repo.category_exists(slug):
        raise ValidationError({'slug': ['Category with this slug already exists.']})

    effective_parent = parent_slug.strip() if parent_slug else None
    if effective_parent:
        if not repo.parent_exists(effective_parent):
            raise NotFound(
                f"Parent category '{effective_parent}' does not exist.",
                code='NOT_FOUND',
            )

        _check_cycle(slug, effective_parent, repo)

    repo.create_category(
        slug=slug,
        name=name,
        parent_slug=effective_parent,
    )

    return get_category_detail(slug=slug, repo=repo)


def get_category_tree(
    root: str | None = None,
    *,
    repo: CategoryRepositoryProtocol = _default_repo,
) -> list[dict[str, Any]]:
    flat = repo.get_category_tree()
    slug_to_node: dict[str, dict[str, Any]] = {}
    for cat in flat:
        slug_to_node[cat.slug] = {
            'slug': cat.slug,
            'name': cat.name,
            'page_count': cat.page_count,
            'children': [],
        }

    roots = []
    for cat in flat:
        node = slug_to_node[cat.slug]
        if cat.parent_slug and cat.parent_slug in slug_to_node:
            slug_to_node[cat.parent_slug]['children'].append(node)
        else:
            roots.append(node)

    if root:
        if root not in slug_to_node:
            raise NotFound(f"Category '{root}' not found.")
        return [slug_to_node[root]]

    return roots


def get_category_detail(
    slug: str,
    raw_page: str | None = None,
    raw_page_size: str | None = None,
    raw_types: str | None = None,
    raw_sort: str | None = None,
    *,
    repo: CategoryRepositoryProtocol = _default_repo,
) -> dict[str, Any]:
    _validate_sort(raw_sort)

    detail = repo.get_category_detail(slug)
    if detail is None:
        raise NotFound(f"Category '{slug}' does not exist.")

    parent = None
    if detail.parent_slug:
        parent = {
            'slug': detail.parent_slug,
            'name': detail.parent_name,
        }

    children = []
    if raw_children := detail.children:
        for child in raw_children:
            if child.slug is not None:
                children.append({
                    'slug': child.slug,
                    'name': child.name,
                    'page_count': child.page_count,
                })

    type_list = None
    if raw_types:
        type_list = [t.strip() for t in raw_types.split(',') if t.strip()]

    page = max(1, _parse_int(raw_page, 1))
    page_size = min(
        MAX_PAGE_SIZE,
        max(1, _parse_int(raw_page_size, DEFAULT_PAGE_SIZE)),
    )
    skip = (page - 1) * page_size

    total_pages_count = repo.count_detail_pages(slug, type_list)

    sort_field = _validate_sort(raw_sort)
    page_rows = repo.list_detail_pages(
        slug, type_list, skip, page_size,
        sort=sort_field, order='asc',
    )

    page_items = [
        {
            'slug': pr.slug,
            'type': pr.type,
            'name': pr.name,
            'image_url': pr.image_url,
        }
        for pr in page_rows
    ]

    total_pages = max(1, (total_pages_count + page_size - 1) // page_size)
    next_page = page + 1 if page < total_pages else None
    prev_page = page - 1 if page > 1 else None

    return {
        'slug': detail.slug,
        'name': detail.name,
        'created_at': detail.created_at,
        'parent_slug': detail.parent_slug,
        'child_count': len(children),
        'page_count': total_pages_count,
        'parent': parent,
        'children': children,
        'pages': {
            'count': total_pages_count,
            'next': next_page if next_page is not None else None,
            'previous': prev_page if prev_page is not None else None,
            'results': page_items,
        },
    }


def update_category(
    slug: str,
    name: str | None = None,
    parent_slug: str | None = None,
    *,
    repo: CategoryRepositoryProtocol = _default_repo,
) -> dict[str, Any]:
    if not repo.category_exists(slug):
        raise NotFound(f"Category '{slug}' does not exist.")

    if name is not None:
        name = name.strip()
        if not name:
            raise ValidationError({'name': ['Name must not be empty.']})
    else:
        old_name = repo.get_name(slug)
        if old_name is None:
            raise NotFound(f"Category '{slug}' does not exist.")
        name = old_name

    if parent_slug is not None:
        _check_cycle(slug, parent_slug, repo)

    repo.update_category(
        slug=slug,
        name=name,
        parent_slug=parent_slug if parent_slug is not None else None,
    )

    return get_category_detail(slug=slug, repo=repo)


def delete_category(
    slug: str,
    *,
    repo: CategoryRepositoryProtocol = _default_repo,
) -> None:
    if not repo.category_exists(slug):
        raise NotFound(f"Category '{slug}' does not exist.")
    repo.delete_category(slug)
