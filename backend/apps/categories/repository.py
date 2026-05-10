'''
Repository layer for the categories app.

Responsibility: translate between Cypher/Neo4j and Python data structures.
No business logic, no HTTP concerns.

Protocols are used so that fake implementations in tests do not need to
inherit from anything - they only need matching method signatures.
'''

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from neomodel import db

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
from apps.categories.utils import neo4j_dt_to_iso, rows_to_dicts
from apps.pages.models import Category


@dataclass(frozen=True)
class CategoryRow:
    '''Flat category representation returned by list/create/update queries.'''
    slug: str
    name: str
    created_at: str | None
    parent_slug: str | None
    child_count: int
    page_count: int


@dataclass(frozen=True)
class CategoryTreeRow:
    '''Row used for building the category tree.'''
    slug: str
    name: str
    parent_slug: str | None
    page_count: int


@dataclass(frozen=True)
class ChildRow:
    '''A direct child category with its page count.'''
    slug: str
    name: str
    page_count: int


@dataclass(frozen=True)
class CategoryDetailRow:
    '''Aggregated detail row returned by CATEGORY_DETAIL_QUERY.'''
    slug: str
    name: str
    created_at: str | None
    parent_slug: str | None
    parent_name: str | None
    children: list[ChildRow]


@dataclass(frozen=True)
class PageSummaryRow:
    '''Minimal page representation used inside category detail.'''
    slug: str
    type: str
    name: str
    image_url: str | None


@runtime_checkable
class CategoryRepositoryProtocol(Protocol):
    '''Interface for the category repository.'''

    def count_categories(self, name: str | None, parent: str | None) -> int:
        ...

    def list_categories(
        self,
        name: str | None,
        parent: str | None,
        skip: int,
        limit: int,
        sort: str = 'slug',
        order: str = 'asc',
    ) -> list[CategoryRow]:
        ...

    def get_category_tree(self) -> list[CategoryTreeRow]:
        ...

    def get_category_detail(self, slug: str) -> CategoryDetailRow | None:
        ...

    def count_detail_pages(self, slug: str, types: list[str] | None) -> int:
        ...

    def list_detail_pages(
        self,
        slug: str,
        types: list[str] | None,
        skip: int,
        limit: int,
        sort: str = 'slug',
        order: str = 'asc',
    ) -> list[PageSummaryRow]:
        ...

    def create_category(
        self,
        slug: str,
        name: str,
        parent_slug: str | None,
    ) -> CategoryRow:
        ...

    def update_category(
        self,
        slug: str,
        name: str,
        parent_slug: str | None,
    ) -> CategoryRow:
        ...

    def delete_category(self, slug: str) -> None:
        ...

    def category_exists(self, slug: str) -> bool:
        ...

    def parent_exists(self, slug: str) -> bool:
        ...

    def would_create_cycle(self, slug: str, parent_slug: str) -> bool:
        ...


class Neo4jCategoryRepository:
    '''Concrete repository for categories backed by Neo4j.'''

    def _row_to_category_row(self, raw: dict) -> CategoryRow:
        '''Convert a raw Cypher result row to a CategoryRow.'''
        return CategoryRow(
            slug=raw['slug'],
            name=raw['name'],
            created_at=neo4j_dt_to_iso(raw.get('created_at')),
            parent_slug=raw['parent_slug'] if raw['parent_slug'] else None,
            child_count=int(raw['child_count']),
            page_count=int(raw['page_count']),
        )

    def _build_order_clause(self, allowed: dict[str, str], sort: str, order: str) -> str:
        '''Build an ORDER BY clause from a whitelist of allowed sort fields.'''
        if sort not in allowed:
            raise ValueError(f"Invalid sort field: {sort}")
        direction = 'ASC' if order.lower() == 'asc' else 'DESC'
        return f'ORDER BY {allowed[sort]} {direction}'

    def count_categories(self, name: str | None, parent: str | None) -> int:
        rows, _ = db.cypher_query(
            CATEGORY_COUNT_QUERY,
            {'name': name, 'parent': parent},
        )
        return int(rows[0][0]) if rows else 0

    def list_categories(
        self,
        name: str | None,
        parent: str | None,
        skip: int,
        limit: int,
        sort: str = 'slug',
        order: str = 'asc',
    ) -> list[CategoryRow]:
        allowed_sorts = {'slug': 'c.slug', 'name': 'c.name'}
        order_clause = self._build_order_clause(allowed_sorts, sort, order)
        query = CATEGORY_LIST_QUERY.replace('ORDER BY c.slug ASC', order_clause)

        rows, meta = db.cypher_query(
            query,
            {'name': name, 'parent': parent, 'skip': skip, 'limit': limit},
        )
        return [
            self._row_to_category_row(r)
            for r in rows_to_dicts(rows, meta)
        ]

    def get_category_tree(self) -> list[CategoryTreeRow]:
        rows, meta = db.cypher_query(CATEGORY_TREE_QUERY, {})
        return [
            CategoryTreeRow(
                slug=r['slug'],
                name=r['name'],
                parent_slug=r['parent_slug'] if r['parent_slug'] else None,
                page_count=int(r['page_count']),
            )
            for r in rows_to_dicts(rows, meta)
        ]

    def get_category_detail(self, slug: str) -> CategoryDetailRow | None:
        rows, meta = db.cypher_query(CATEGORY_DETAIL_QUERY, {'slug': slug})
        if not rows:
            return None
        raw = rows_to_dicts(rows, meta)[0]
        children = [
            ChildRow(
                slug=c['slug'],
                name=c['name'],
                page_count=int(c['page_count']),
            )
            for c in (raw['children'] or [])
        ] if raw['children'] else []

        return CategoryDetailRow(
            slug=raw['slug'],
            name=raw['name'],
            created_at=neo4j_dt_to_iso(raw.get('created_at')),
            parent_slug=raw['parent_slug'] if raw['parent_slug'] else None,
            parent_name=raw['parent_name'] if raw.get('parent_name') else None,
            children=children,
        )

    def count_detail_pages(self, slug: str, types: list[str] | None) -> int:
        rows, _ = db.cypher_query(
            CATEGORY_DETAIL_PAGES_COUNT_QUERY,
            {'slug': slug, 'types': types},
        )
        return int(rows[0][0]) if rows else 0

    def list_detail_pages(
        self,
        slug: str,
        types: list[str] | None,
        skip: int,
        limit: int,
        sort: str = 'slug',
        order: str = 'asc',
    ) -> list[PageSummaryRow]:
        allowed_sorts = {'slug': 'page.slug', 'name': 'page.names[0]'}
        order_clause = self._build_order_clause(allowed_sorts, sort, order)
        query = CATEGORY_DETAIL_PAGES_QUERY.replace('ORDER BY page.slug ASC', order_clause)

        rows, meta = db.cypher_query(
            query,
            {'slug': slug, 'types': types, 'skip': skip, 'limit': limit},
        )
        return [
            PageSummaryRow(
                slug=r['slug'],
                type=r['type'],
                name=r['name'],
                image_url=r.get('image_url'),
            )
            for r in rows_to_dicts(rows, meta)
        ]

    def create_category(
        self,
        slug: str,
        name: str,
        parent_slug: str | None,
    ) -> CategoryRow:
        rows, meta = db.cypher_query(
            CATEGORY_CREATE_QUERY,
            {'slug': slug, 'name': name, 'parent_slug': parent_slug},
        )
        return self._row_to_category_row(
            rows_to_dicts(rows, meta)[0]
        )

    def update_category(
        self,
        slug: str,
        name: str,
        parent_slug: str | None,
    ) -> CategoryRow:
        rows, meta = db.cypher_query(
            CATEGORY_UPDATE_QUERY,
            {'slug': slug, 'name': name, 'parent_slug': parent_slug},
        )
        return self._row_to_category_row(
            rows_to_dicts(rows, meta)[0]
        )

    def delete_category(self, slug: str) -> None:
        db.cypher_query(CATEGORY_DELETE_QUERY, {'slug': slug})

    def category_exists(self, slug: str) -> bool:
        return Category.nodes.filter(slug=slug).exists()

    def parent_exists(self, slug: str) -> bool:
        return Category.nodes.filter(slug=slug).exists()

    def would_create_cycle(self, slug: str, parent_slug: str) -> bool:
        rows, _ = db.cypher_query(
            CYCLE_CHECK_QUERY,
            {'slug': slug, 'parent_slug': parent_slug},
        )
        return bool(rows and rows[0][0])


_default_repo = Neo4jCategoryRepository()
