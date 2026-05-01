'''
Business logic for /pages/{slug}/comments/ endpoints.

Author enrichment:
  The Neo4j :User node stores only django_id. Username and avatar_url live
  in Django's SQLite DB. The service returns raw author_django_id rows and
  the view enriches them in bulk (one SQL query for all authors in a page)
  rather than N+1 queries. This is the same pattern the likes endpoint uses.
'''

from typing import Any

from neomodel import db  # type: ignore[attr-defined]
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from apps.users.models import User

from .queries import (
    COMMENT_COUNT_QUERY,
    COMMENT_CREATE_QUERY,
    COMMENT_DELETE_QUERY,
    COMMENT_FETCH_AUTHOR_QUERY,
    COMMENT_LIST_QUERY,
    COMMENT_UPDATE_QUERY,
    PAGE_EXISTS_QUERY,
)

MAX_COMMENT_LENGTH = 300


# Internal helpers

def _assert_page_exists(slug: str) -> None:
    '''Raise NotFound if no :Page node with this slug exists'''
    resilts, _ = db.cypher_query(PAGE_EXISTS_QUERY, {'slug': slug})

    if not resilts:
        raise NotFound(
            detail=f'Page "{slug}" does not exist.',
            code='NOT_FOUND',
        )


def _neo4j_dt_to_iso(dt: Any) -> str | None:
    '''Convert a Neo4j DateTime object to an ISO-8601 string, or None'''
    if dt is None:
        return None

    if hasattr(dt, 'isoformat'):
        return dt.isoformat()

    return str(dt)


def _build_author_map(django_ids: list[int]) -> dict[int, dict[str, Any]]:
    '''
    Bulk-fetch username + avatar_url from SQLite for a list of django user ids.
    Returns {django_id: {username, avatar_url}}.

    Missing ids (e.g. deleted users) are mapped to a sentinel 'deleted' author
    so the comment list endpoint never breaks.
    '''
    if not django_ids:
        return {}

    users = (
        User.objects
        .filter(pk__in=django_ids)
        .values('id', 'username', 'avatar_url')
    )

    return {
        u['id']: {
            'username': u['username'],
            'avatar_url': u['avatar_url'] or None,
        }
        for u in users
    }


def _enrich_row(
    row: dict[str, Any],
    author_map: dict[int, dict[str, Any]]
) -> dict[str, Any]:
    '''
    Merge a raw Cypher result row with author data from the author_map.
    Falls back gracefully if the Django user no longer exists.
    '''
    django_id: int | None = row.get('author_django_id')
    sentinel = {
        'username': '[deleted]',
        'avatar_url': None,
    }
    author = author_map.get(django_id or -1) or sentinel

    return {
        'id': row['id'],
        'text': row['text'],
        'author': author,
        'created_at': _neo4j_dt_to_iso(row.get('created_at')),
        'updated_at': _neo4j_dt_to_iso(row.get('updated_at')),
    }


# Public service functions


def list_comments(
        slug: str,
        page: int,
        page_size: int,
) -> dict[str, Any]:
    '''
    Return a paginated list of comments for the given page slug.

    Does NOT check page existence first - if the page is missing, the COUNT
    query returns 0 and results is empty, which is indistinguishable from a
    page with no comments from the DB's perspective. We do a pre-flight check
    here so clients get a 404 instead of an empty list.
    '''
    _assert_page_exists(slug)

    skip = (page - 1) * page_size

    count_rows, _ = db.cypher_query(COMMENT_COUNT_QUERY, {'slug': slug})
    total = int(count_rows[0][0] if count_rows else 0)

    if total == 0:
        return {
            'count': 0,
            'next': None,
            'previous': None,
            'results': [],
        }

    rows, meta = db.cypher_query(
        COMMENT_LIST_QUERY,
        {
            'slug': slug,
            'skip': skip,
            'limit': page_size,
        }
    )
    raw_rows = [dict(zip(meta, row, strict=True)) for row in rows]

    # Bulk author enrichment
    django_ids = [r['author_django_id'] for r in raw_rows if r.get('author_django_id')]
    author_map = _build_author_map(django_ids)

    results = [_enrich_row(r, author_map) for r in raw_rows]

    # Pagination URLs
    total_pages = max(1, (total + page_size - 1) // page_size)
    next_page = page + 1 if page < total_pages else None
    prev_page = page - 1 if page > 1 else None

    return {
        "count": total,
        "next": next_page,
        "previous": prev_page,
        "results": results,
    }


def create_comment(
        slug: str,
        text: str,
        requesting_django_id: int,
) -> dict[str, Any]:
    '''Create a comment on the given page.'''
    _assert_page_exists(slug)

    text = text.strip()
    if not text:
        raise ValidationError(
            {
                'text': ['Comment text must not be empty.']
            }
        )
    if len(text) > MAX_COMMENT_LENGTH:
        raise ValidationError(
            {
                'text': [
                    f'Comment nust be at most {MAX_COMMENT_LENGTH} characters long.'
                ]
            }
        )

    rows, meta = db.cypher_query(
        COMMENT_CREATE_QUERY,
        {
            'slug': slug,
            'django_id': requesting_django_id,
            'text': text,
        },
    )

    raw = dict(zip(meta, rows[0], strict=True))
    author_map = _build_author_map([requesting_django_id])

    return _enrich_row(raw, author_map)


def delete_comment(
        slug: str,
        comment_id: str,
        requesting_django_id: int,
        is_admin: bool,
) -> None:
    '''
    Delete a comment.

    Ownership check:
        - Admin: may delete any comment.
        - Viewer: may only delete their own comment.
    '''
    _assert_page_exists(slug)

    rows, meta = db.cypher_query(
        COMMENT_FETCH_AUTHOR_QUERY,
        {
            'slug': slug,
            'comment_id': comment_id,
        },
    )

    if not rows:
        raise NotFound(
            detail=f'Comment "{comment_id}" not found on page "{slug}".',
            code='NOT_FOUND',
        )

    row = dict(zip(meta, rows[0], strict=True))
    author_django_id: int = row["author_django_id"]

    if not is_admin and author_django_id != requesting_django_id:
        raise PermissionDenied(
            detail='You can only delete your own comments.',
            code='FORBIDDEN',
        )

    db.cypher_query(
        COMMENT_DELETE_QUERY,
        {
            'slug': slug,
            'comment_id': comment_id,
        },
    )


def update_comment(
        slug: str,
        comment_id: str,
        text: str,
        requesting_django_id: int,
) -> dict[str, Any]:
    rows, meta = db.cypher_query(
        COMMENT_FETCH_AUTHOR_QUERY,
        {
            "slug": slug,
            "comment_id": comment_id,
        },
    )

    if not rows:
        raise NotFound(
            detail=f'Comment "{comment_id}" not found on page "{slug}".',
            code='NOT_FOUND',
        )

    row = dict(zip(meta, rows[0], strict=True))
    author_django_id: int = row['author_django_id']

    if author_django_id != requesting_django_id:
        raise PermissionDenied(
            detail='You can only edit your own comments.',
            code='FORBIDDEN',
        )

    text = text.strip()
    if not text:
        raise ValidationError(
            {
                'text': ['Comment text must not be empty.']
            }
        )
    if len(text) > MAX_COMMENT_LENGTH:
        raise ValidationError(
            {
                'text': [f'Comment must be at most {MAX_COMMENT_LENGTH} characters.']
            }
        )

    update_rows, meta = db.cypher_query(
        COMMENT_UPDATE_QUERY,
        {
            'slug': slug,
            'comment_id': comment_id,
            'text': text,
        },
    )

    raw = dict(zip(meta, update_rows[0], strict=True))
    author_map = _build_author_map([requesting_django_id])

    return _enrich_row(raw, author_map)
