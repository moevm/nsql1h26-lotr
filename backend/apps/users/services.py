'''
Business logic for the users app.

Separation of concerns:
    - get_liked_pages() - used by /auth/me/ (flat list, no pagination)
    - get_user_neo4j_stats() - used by GET /users/{username}/ (profile preview)
    - build_public_profile() - assembles the full public profile dict
    - get_liked_pages_paginated() - used by GET /users/{username}/liked/
    - delete_user_and_cleanup() - used by DELETE /users/{username}/

TODO: implement REPOSITORY
'''


from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

from neomodel import db
from rest_framework.exceptions import PermissionDenied

from apps.pages.queries import labels_to_type  # type: ignore[attr-defined]

from .models import User
from .queries import (
    DELETE_USER_NEO4J_QUERY,
    GET_LIKED_PAGES_COUNT_QUERY,
    GET_LIKED_PAGES_PAGINATED_QUERY,
    GET_USER_NEO4J_STATS_QUERY,
)


# TODO: move into core or something, so DRY (c.f. catalogs, etc.) 
@dataclass
class PaginatedResult:
    count: int
    next: str | None
    previous: str | None
    results: list[dict[str, Any]]


# Internal helpers


def _build_pagination_urls(
    base_url: str,
    filter_params: dict[str, Any],
    page: int,
    page_size: int,
    total: int,
) -> tuple[str | None, str | None]:
    '''Builds URL for next/previous while saving all filters'''
    total_pages = max(1, (total + page_size - 1) // page_size)

    def _url(p: int) -> str:
        params = {**filter_params, 'page': p, 'page_size': page_size}
        return f'{base_url}?{urlencode(params)}'

    next_url = _url(page + 1) if page < total_pages else None
    prev_url = _url(page - 1) if page > 1 else None

    return next_url, prev_url


def _row_to_page_summary(
    slug: str,
    node_labels: list[str],
    name: str | None,
    image_url: str | None,
) -> dict[str, Any]:
    entity_type = labels_to_type(node_labels or [])

    return {
        'slug': slug,
        'type': entity_type.value if entity_type else 'unknown',
        'name': name or '',
        'image_url': image_url,
    }


# def get_liked_pages(user_id: int) -> list[dict[str, Any]]:
#     '''
#     Returns pages liked by the user (Neo4j).
#     Keeps serializers SQL-only.
#     '''

#     query = """\
#     MATCH (u:User {django_id: $user_id})-[:LIKED]->(p:Page)
#     RETURN p.slug AS slug, p.names[0] AS name
#     ORDER BY p.names[0]
#     """
#     results, _ = db.cypher_query(query, {'user_id': user_id})

#     if not results:
#         return []

#     return [{'slug': row[0], 'name': row[1]} for row in results]


# GET /users/{username}/liked/ - paginated liked pages
def get_liked_pages(
    django_id: int,
    page: int,
    page_size: int,
    base_url: str,
    filter_params: dict[str, Any],
) -> PaginatedResult:
    '''
    Returns a paginated PaginatedResult of PageSummary dicts.

    Two-query approach (count then fetch) keeps SKIP/LIMIT logic simple and
    avoids running COUNT over a SKIP result which can mislead in Cypher.

    If the user has no Neo4j node, returns an empty result (count=0).
    '''
    count_rows, _ = db.cypher_query(
        GET_LIKED_PAGES_COUNT_QUERY,
        {
            'django_id': django_id
        }
    )
    total: int = count_rows[0][0] if count_rows else 0

    next_url, prev_url = _build_pagination_urls(
        base_url,
        filter_params,
        page,
        page_size,
        total,
    )

    if total == 0:
        return PaginatedResult(count=0, next=None, previous=None, results=[])

    skip = (page - 1) * page_size
    rows, _ = db.cypher_query(
        GET_LIKED_PAGES_PAGINATED_QUERY,
        {
            'django_id': django_id,
            'skip': skip,
            'limit': page_size,
        },
    )

    results = [
        _row_to_page_summary(
            slug=row[0],
            node_labels=row[1],
            name=row[2],
            image_url=row[3],
        )
        for row in rows
    ]

    return PaginatedResult(
        count=total,
        next=next_url,
        previous=prev_url,
        results=results,
    )


# GET /users/{username}/ – public profile
def get_user_neo4j_stats(django_id: int) -> dict[str, Any]:
    '''
    Fetches Neo4j statistics for a user's public profile in a single query:

    If the user has no Neo4j node (they exist in Django but have never
    commented or liked anything), returns zeroed stats with an empty list.
    This is the normal state for a new or inactive user.
    '''
    results, _ = db.cypher_query(
        GET_USER_NEO4J_STATS_QUERY, {'django_id': django_id}
    )

    # Empty result -> user has no Neo4j node yet
    if not results:
        return {
            'comments_count': 0,
            'liked_pages_total': 0,
            'liked_pages': [],
        }

    # All rows share the same aggregate counts (they differ only in page data)
    first_row = results[0]
    comments_count: int = first_row[0]
    liked_pages_total: int = first_row[1]

    liked_pages: list[dict[str, Any]] = []
    for row in results:
        slug = row[2]
        if slug is not None:
            liked_pages.append(
                _row_to_page_summary(
                    slug=slug,
                    node_labels=row[3],
                    name=row[4],
                    image_url=row[5],
                )
            )

    return {
        'comments_count': comments_count,
        'liked_pages_total': liked_pages_total,
        'liked_pages': liked_pages,
    }


def build_public_profile(user: User) -> dict[str, Any]:
    '''
    Assembles the full public profile response dict for one user.
    '''
    neo4j_stats = get_user_neo4j_stats(user.pk)

    return {
        'username': user.username,
        'avatar_url': user.avatar_url,
        'created_at': user.date_joined,
        **neo4j_stats,  # comments_count, liked_pages_total, liked_pages
    }


# DELETE /users/{username}/ - delete user + Neo4j cleanup
def delete_user_and_cleanup(requesting_user: User, target_username: str) -> None:
    '''
    Deletes a user account and cleans up their Neo4j data.

    Raises PermissionDenied if the requesting admin tries to delete themselves

    If the user never interacted with the graph (no Neo4j node), the
    OPTIONAL MATCH + DETACH DELETE is safe.

    IMPORTANT: The view is responsible for calling get_object_or_404 BEFORE
    this function so that a missing username surfaces as a 404, not a silent
    no-op.
    '''
    if requesting_user.username == target_username:
        raise PermissionDenied('You cannot delete your own account.')

    user = User.objects.filter(username=target_username).first()
    if user is None:
        return

    django_id = user.pk

    db.cypher_query(DELETE_USER_NEO4J_QUERY, {'django_id': django_id})
    user.delete()
