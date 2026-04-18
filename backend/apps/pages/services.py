'''
Transaction note:
    neomodel wraps all db.cypher_query calls in implicit transactions.
    For multi-step mutations we use `with db.transactions:` to guarantee
    atomicity. If any step raises, the entire transaction is rolled back.
'''

from typing import Any

from neomodel import db  # type: ignore[attr-defined]
from rest_framework.exceptions import NotFound, ValidationError

from .queries import (
    ALLOWED_REL_TYPES,
    PAGE_ARTICLE_UPSERT_QUERY,
    PAGE_ATTRS_UPDATE_QUERY,
    PAGE_CATEGORIES_REPLACE_QUERY,
    PAGE_DELETE_QUERY,
    PAGE_DETAIL_QUERY,
    PAGE_RELS_CREATE_TEMPLATE,
    PAGE_RELS_DELETE_TEMPLATE,
    build_attributes_for_response,
    labels_to_type,
    normalize_patch_attributes,
)


# Internal helpers

def _target_summary(item: dict[str, Any]) -> dict[str, Any]:
    '''
    Build a relation-targer summary object from a collected map.

    The map is produced by the CALL subquery in PAGE_DETAIL_QUERY.
    targetLabels is a list like ['Page', 'Character']. We extract the type.
    '''

    entity_type = labels_to_type(item.get('targetLabels') or [])
    names: list[str] = item.get('targetNames') or []

    return {
        'slug': item.get('targetSlug'),
        'type': entity_type,
        'name': names[0] if names else None,
        'imageUrl': item.get('targetImageUrl'),
    }


def _source_summary(item: dict[str, Any]) -> dict[str, Any]:
    '''Build a relation-source summary (for incoming edges)'''

    entity_type = labels_to_type(item.get('sourceLabels') or [])
    names: list[str] = item.get('sourceNames') or []

    return {
        'slug': item.get('sourceSlug'),
        'type': entity_type,
        'name': names[0] if names else None,
        'imageUrl': item.get('sourceImageUrl')
    }


def _build_relations(
        outgoing_rels: list[dict],
        incoming_rels: list[dict],
) -> dict[str, dict]:
    '''
    Group raw rel rows into the nested outgoing/incoming structure

    Output:
    {
        "outgoing": {
            "MEMBER_OF": [{"target": {...}, "properties": {...}}],
            ...
        },
        "incoming": {
            "CHILD_OF": [{"from": {...}, "properties": {...}}],
            ...
        }
    }
    '''
    outgoing: dict[str, list] = {}
    for item in outgoing_rels:
        if item is None:
            continue
        rel_type = item.get("relType", "UNKNOWN")
        entry = {
            "target":     _target_summary(item),
            "properties": item.get("relProps") or {},
        }
        outgoing.setdefault(rel_type, []).append(entry)

    incoming: dict[str, list] = {}
    for item in incoming_rels:
        if item is None:
            continue
        rel_type = item.get("relType", "UNKNOWN")
        entry = {
            "from":       _source_summary(item),
            "properties": item.get("relProps") or {},
        }
        incoming.setdefault(rel_type, []).append(entry)

    return {"outgoing": outgoing, "incoming": incoming}


def _row_to_page_dict(row: dict[str, Any]) -> dict[str, Any]:
    '''Convert a raw query result row into the page response dict'''
    props: dict = row['props'] or {}
    node_labels: list[str] = row['node_labels'] or []
    article_props: dict | None = row['article_props']

    entity_type = labels_to_type(node_labels) or 'unknown'
    names: list[str] = props.get('names') or []

    attributes = build_attributes_for_response(props, entity_type)

    article: dict | None = None
    if article_props:
        created_at = article_props.get("createdAt")
        updated_at = article_props.get("updatedAt")
        article = {
            "text":      article_props.get("text"),
            "imageUrl":  article_props.get("imageUrl"),
            "createdAt": created_at.isoformat() if hasattr(created_at, "isoformat") else created_at,
            "updatedAt": updated_at.isoformat() if hasattr(updated_at, "isoformat") else updated_at,
        }

    relations = _build_relations(
        row.get("outgoing_rels") or [],
        row.get("incoming_rels") or [],
    )

    likes_count = row.get("likes_count") or 0
    comments_count = row.get("comments_count") or 0
    is_liked = row.get("is_liked")

    return {
        "slug": props.get("slug"),
        "type": entity_type,
        "names": names,
        "name": names[0] if names else None,
        "attributes": attributes,
        "article": article,
        "relations": relations,
        "categories": row.get("categories") or [],
        "likesCount": likes_count,
        "isLiked": is_liked,
        "commentsCount": comments_count,
    }


# Public service functions

def get_page(slug: str, user_id: int | None = None) -> dict[str, Any]:
    '''
    Fetch full page data for GET /pages/{slug}/.
    '''

    results, meta = db.cypher_query(
        PAGE_DETAIL_QUERY,
        {
            'slug': slug,
            'user_id': user_id,
        }
    )

    if not results:
        raise NotFound(
            detail=f'Page \'{slug}\' does not exist',
            code='NOT_FOUND'
        )

    row = dict(zip(meta, results[0]))
    return _row_to_page_dict(row)


def _update_node_attrs(slug: str, raw_attrs: dict, entity_type: str) -> None:
    '''Apply partial node property update'''

    if not raw_attrs:
        return

    db_attrs = normalize_patch_attributes(raw_attrs, entity_type)
    if db_attrs:
        db.cypher_query(
            PAGE_ATTRS_UPDATE_QUERY,
            {
                'slug': slug,
                'attrs': db_attrs
            },
        )


def _update_names(slug: str, names: list[str]) -> None:
    '''Update the top-level `names` property'''
    db.cypher_query(
        'MATCH (p:Page {slug: $slug}) SET p.names = $names',
        {
            'slug': slug,
            'names': names
        },
    )


def _upsert_article(slug: str, article: dict) -> None:
    '''Create or update the article node'''
    db.cypher_query(
        PAGE_ARTICLE_UPSERT_QUERY,
        {
            'slug': slug,
            'text': article.get('text') or '',
            'image_url': article.get('imageUrl'),
        },
    )


def _replace_categories(slug: str, cat_slugs: list[str]) -> None:
    '''Delete all existing IN_CATEGORY edges and create the new ones'''
    if cat_slugs:
        db.cypher_query(
            PAGE_CATEGORIES_REPLACE_QUERY,
            {
                'slug': slug,
                'cat_slugs': cat_slugs,
            },
        )
    else:
        # Just delete - no new ones to create
        db.cypher_query(
            'MATCH (p:Page {slug: $slug})-[r:IN_CATEGORY]->() DELETE r',
            {
                'slug': slug
            },
        )


def _update_relations(slug: str, relations: dict) -> None:
    """
    For each relationship type in the patch payload:
      1. Delete all existing outgoing rels of that type.
      2. Create new rels to the specified targets.

    rel_type is validated against ALLOWED_REL_TYPES before interpolation.
    Unknown types raise a validation error (prevents silent data corruption
    and Cypher injection).
    """

    invalid = set(relations.keys()) - ALLOWED_REL_TYPES
    if invalid:
        raise ValidationError(
            {
                "relations": [
                    f"Unknown relation type(s): {', '.join(sorted(invalid))}. "
                    f"Allowed: {', '.join(sorted(ALLOWED_REL_TYPES))}"
                ]
            }
        )

    for rel_type, targets in relations.items():
        # Delete existing rels of this type
        delete_q = PAGE_RELS_DELETE_TEMPLATE.format(rel_type=rel_type)
        db.cypher_query(delete_q, {"slug": slug})

        # Create new rels (skip if the list is empty - this means "delete all")
        if targets:
            create_q = PAGE_RELS_CREATE_TEMPLATE.format(rel_type=rel_type)
            db.cypher_query(
                create_q,
                {
                    "slug": slug,
                    "targets": [
                        {
                            "slug": t["slug"],
                            "properties": t.get("properties") or {},
                        }
                        for t in targets
                    ],
                },
            )


def update_page(
        slug: str,
        validated_data: dict,
        user_id: int | None = None,
) -> dict[str, Any]:
    '''Apply a partial update and return the refreshed page.'''

    results, _ = db.cypher_query(
        'MATCH (p:Page {slug: $slug}) RETURN labels(p) AS node_labels LIMIT 1',
        {
            'slug': slug,
        },
    )

    if not results:
        raise NotFound(
            detail=f'Page \'{slug}\' does not exist.',
            code='NOT_FOUND',
        )

    entity_type = labels_to_type(results[0][0]) or 'unknown'

    relations: dict = validated_data.get('relations') or {}
    if relations:
        invalid = set(relations.keys()) - ALLOWED_REL_TYPES
        if invalid:
            raise ValidationError(
                {
                    'relations': [
                        f'Unknown relation type(s): '
                        f'{", ".join(sorted(invalid))}.'
                    ]
                }
            )

    with db.transaction:
        names: list | None = validated_data.get('names')
        if names is not None:
            _update_names(slug, names)

        raw_attrs: dict = validated_data.get('attributes') or {}
        if raw_attrs:
            _update_node_attrs(slug, raw_attrs, entity_type)

        article: dict | None = validated_data.get('article')
        if article is not None:
            _upsert_article(slug, article)

        categories: list | None = validated_data.get('categories')
        if categories is not None:
            _replace_categories(slug, categories)

        if relations:
            _update_relations(slug, relations)

    # Re-fetch after commit to return the canonical representation
    return get_page(slug, user_id=user_id)


def delete_page(slug: str) -> None:
    '''
    Delete a page ode, its article node, and all edges.

    DETACH DELETE removes all edges from/to the page.
    The article node is explicitly deleted to avoid orphaned nodes (it has no
    :Page label so it would not be found by any MATCH on :Page)
    '''

    results, _ = db.cypher_query(
        'MATCH (p:Page {slug: $slug}) RETURN p.slug LIMIT 1',
        {
            'slug': slug,
        },
    )
    if not results:
        raise NotFound(
            detail=f'Page \'{slug}\' does not exists.',
            code='NOT_FOUND',
        )

    db.cypher_query(PAGE_DELETE_QUERY, {'slug': slug})
