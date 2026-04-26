'''
Business logic for GET / PATCH / DELETE /pages/{slug}/.

Layer responsibilities:
  services.py - all Neo4j interaction and domain logic
  views.py - HTTP parsing, permissions, response assembly only
  queries.py - Cypher string constants and type metadata

Transaction note:
    neomodel wraps all db.cypher_query calls in implicit transactions.
    For multi-step mutations we use `with db.transactions:` to guarantee
    atomicity. If any step raises, the entire transaction is rolled back.
    All pre-flight validation (slug existence, relation type whitelist, target
    slug existence) is performed BEFORE entering the transaction block so that
    user errors surface as clean 4xx responses without a partial write.
'''

from typing import Any, Literal

from neomodel import db  # type: ignore[attr-defined]
from rest_framework.exceptions import NotFound, ValidationError

from .enums import EntityType
from .queries import (
    ALLOWED_REL_TYPES,
    CATEGORY_SLUGS_EXISTS_QUERY,
    PAGE_ARTICLE_UPSERT_QUERY,
    PAGE_ATTRS_UPDATE_QUERY,
    PAGE_CATEGORIES_CLEAR_QUERY,
    PAGE_CATEGORIES_REPLACE_QUERY,
    PAGE_DELETE_ALL_INCOMING_RELS_QUERY,
    PAGE_DELETE_ALL_OUTGOING_RELS_QUERY,
    PAGE_DELETE_QUERY,
    PAGE_DETAIL_QUERY,
    PAGE_FETCH_LABELS_QUERY,
    PAGE_LIKE_ADD_QUERY,
    PAGE_LIKE_REMOVE_QUERY,
    PAGE_NAMES_UPDATE_QUERY,
    PAGE_RELS_INCOMING_CREATE_TEMPLATE,
    PAGE_RELS_INCOMING_DELETE_TEMPLATE,
    PAGE_RELS_OUTGOING_CREATE_TEMPLATE,
    PAGE_RELS_OUTGOING_DELETE_TEMPLATE,
    PAGE_SLUGS_WITH_LABELS_QUERY,
    REL_DIRECTION_ALLOWED_TYPES,
    build_attributes_for_response,
    labels_to_type,
    normalize_patch_attributes,
    sanitize_rel_properties,
)

_CREATE_NODE_TEMPLATE = """\
CREATE (n:{node_labels} {{slug: $slug, names: $names}})
SET n += $attrs
"""


# Response assembly helpers

def _node_summary(
        item: dict[str, Any],
        prefix: Literal['source', 'target']
) -> dict[str, Any]:
    '''
    Build a page summary from a collected relation map.

    `prefix` is either "target" (outgoing) or "source" (incoming), matching
    the key names returned by the CALL subqueries in PAGE_DETAIL_QUERY.
    '''
    entity_type = labels_to_type(item.get(f'{prefix}Labels') or [])
    names: list[str] = item.get(f'{prefix}Names') or []

    return {
        'slug': item.get(f'{prefix}Slug'),
        'type': entity_type,
        'name': names[0] if names else None,
        'image_url': item.get(f'{prefix}ImageUrl'),
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
            "target": _node_summary(item, 'target'),
            "properties": item.get("relProps") or {},
        }
        outgoing.setdefault(rel_type, []).append(entry)

    incoming: dict[str, list] = {}
    for item in incoming_rels:
        if item is None:
            continue
        rel_type = item.get("relType", "UNKNOWN")
        entry = {
            "from": _node_summary(item, 'source'),
            "properties": item.get("relProps") or {},
        }
        incoming.setdefault(rel_type, []).append(entry)

    return {"outgoing": outgoing, "incoming": incoming}


def _row_to_page_dict(row: dict[str, Any]) -> dict[str, Any]:
    '''Convert a raw query result row into the page response dict'''
    props: dict = row['props'] or {}
    node_labels: list[str] = row['node_labels'] or []
    article_props: dict | None = row['article_props']

    entity_type = labels_to_type(node_labels) or EntityType.CHARACTER
    names: list[str] = props.get('names') or []

    article: dict | None = None
    if article_props:
        created_at = article_props.get("createdAt")
        updated_at = article_props.get("updatedAt")
        article = {
            "text":      article_props.get("text"),
            "image_url":  article_props.get("imageUrl"),

            # TODO: check if it works or always fallbacks
            "created_at": created_at.isoformat() if hasattr(created_at, "isoformat") else created_at,
            "updated_at": updated_at.isoformat() if hasattr(updated_at, "isoformat") else updated_at,
        }

    attributes = build_attributes_for_response(props, entity_type)
    relations = _build_relations(
        row.get("outgoing_rels") or [],
        row.get("incoming_rels") or [],
    )
    likes_count = row.get("likes_count") or 0
    is_liked = row.get("is_liked")
    comments_count = row.get("comments_count") or 0

    return {
        "slug": props.get("slug"),
        "type": entity_type,
        "names": names,
        "name": names[0] if names else None,
        "attributes": attributes,
        "article": article,
        "relations": relations,
        "categories": row.get("categories") or [],
        "likes_count": likes_count,
        "is_liked": is_liked,
        "comments_count": comments_count,
    }


# Pre-flight validation helpers

def _fetch_and_validate_page_types(
        slugs: list[str],
        field: str = 'relations',
) -> dict[str, EntityType]:
    '''
    Batch-check that all slugs exist as :Page nodes AND return their entity
    types.  One DB round-trip replaces the old two-step pattern of
    `_validate_page_slugs_exist` + a second type-lookup query.
    '''
    if not slugs:
        return {}

    results, _ = db.cypher_query(
        PAGE_SLUGS_WITH_LABELS_QUERY, {'slugs': list(set(slugs))}
    )
    slug_to_type = {
        row[0]: labels_to_type(row[1] or []) or EntityType.CHARACTER
        for row in results
    }

    missing = sorted(s for s in slugs if s not in slug_to_type)
    if missing:
        raise ValidationError(
            {field: [f'Page(s) not found: {", ".join(missing)}']}
        )

    return slug_to_type


def _validate_category_slugs_exist(slugs: list[str]) -> None:
    '''
    Batch-check that all given slugs exist as :Category nodes in one round-trip
    '''
    if not slugs:
        return

    results, _ = db.cypher_query(CATEGORY_SLUGS_EXISTS_QUERY, {'slugs': slugs})
    missing = sorted(row[0] for row in results if not row[1])
    if missing:
        raise ValidationError(
            {'categories': [f'Page(s) not found: {", ".join(missing)}']}
        )


def _validate_rel_types(
        relations: dict,
        direction_label: Literal['incoming', 'outgoing']) -> None:
    """
    Verify all relationship type keys are in the allowed whitelist.

    Rel type names are interpolated into Cypher strings in _apply_relations(),
    so only whitelisted names may be used.
    """
    invalid = set(relations.keys()) - ALLOWED_REL_TYPES
    if invalid:
        raise ValidationError(
            {
                f'relations.{direction_label}': [
                    f'Unknown relation type(s): {", ".join(sorted(invalid))}. '
                    f'Allowed: {", ".join(sorted(ALLOWED_REL_TYPES))}'
                ]
            }
        )


def _validate_rel_types_for_entity(
        entity_type: EntityType,
        outgoing: dict,
        incoming: dict,
) -> None:
    '''
    Check that each relationship type is compatible with the current node's
    entity type without requiring any DB lookup.

    This is a cheap pre-flight guard; endpoint-type validation (checking each
    target/source slug's type) is done separately in
    _validate_rel_endpoint_types after slugs are fetched from the DB.
    '''
    errors: dict[str, list[str]] = {}

    for rel_type in outgoing:
        constraint = REL_DIRECTION_ALLOWED_TYPES.get(rel_type)
        if constraint and entity_type not in constraint['from']:
            errors[f'relations.outgoing.{rel_type}'] = [
                f'Relation {rel_type} cannot originate from a {entity_type}. '
                f'Allowed source types: {sorted(constraint["from"])}.'
            ]

    for rel_type in incoming:
        constraint = REL_DIRECTION_ALLOWED_TYPES.get(rel_type)
        if constraint and entity_type not in constraint['to']:
            errors[f'relations.incoming.{rel_type}'] = [
                f'Relation {rel_type} cannot terminate at a {entity_type}. '
                f'Allowed target types: {sorted(constraint["to"])}.'
            ]

    if errors:
        raise ValidationError(errors)


def _validate_rel_endpoint_types(
        outgoing: dict,
        incoming: dict,
        slug_to_type: dict[str, str],
) -> None:
    '''
    Check that each target/source slug has the correct entity type for its
    relationship type.

    Called after _validate_rel_types_for_entity (which checks the current
    node) and after _fetch_and_validate_page_types (which confirms existence).
    '''
    errors: dict[str, list[str]] = {}

    for rel_type, targets in outgoing.items():
        constraint = REL_DIRECTION_ALLOWED_TYPES.get(rel_type)
        if not constraint:
            # unknown rel_types already rejected by _validate_rel_types
            continue

        for t in targets:
            target_type = slug_to_type.get(t['slug'], 'unknown')
            if target_type not in constraint['to']:
                errors.setdefault(f'relations.outgoing.{rel_type}', []).append(
                    f"Target '{t['slug']}' is a {target_type}. "
                    f"Relation {rel_type} requires a target of type: "
                    f"{sorted(constraint['to'])}."
                )

    for rel_type, sources in incoming.items():
        constraint = REL_DIRECTION_ALLOWED_TYPES.get(rel_type)
        if not constraint:
            continue

        for s in sources:
            source_type = slug_to_type.get(s['slug'], 'unknown')
            if source_type not in constraint['from']:
                errors.setdefault(f'relations.incoming.{rel_type}', []).append(
                    f"Source '{s['slug']}' is a {source_type}. "
                    f"Relation {rel_type} requires a source of type: "
                    f"{sorted(constraint['from'])}."
                )

    if errors:
        raise ValidationError(errors)


def _preflight_relations(
    entity_type: EntityType,
    outgoing: dict | None,
    incoming: dict | None,
) -> dict[str, Any]:
    '''
    Run all relation pre-flight checks.  Returns slug_to_type mapping.
    Called both from update_page() and create_full_page().
    '''
    if outgoing:
        _validate_rel_types(outgoing, 'outgoing')
    if incoming:
        _validate_rel_types(incoming, 'incoming')

    if outgoing is not None or incoming is not None:
        _validate_rel_types_for_entity(
            entity_type,
            outgoing or {},
            incoming or {},
        )

    outgoing_slugs: list[str] = [
        t['slug'] for targets in (outgoing or {}).values() for t in targets
    ]
    incoming_slugs: list[str] = [
        s["slug"] for sources in (incoming or {}).values() for s in sources
    ]

    slug_to_type: dict[str, Any] = {}
    if outgoing_slugs:
        slug_to_type.update(
            _fetch_and_validate_page_types(outgoing_slugs, 'relations.outgoing')
        )
    if incoming_slugs:
        slug_to_type.update(
            _fetch_and_validate_page_types(incoming_slugs, "relations.incoming")
        )

    if outgoing_slugs or incoming_slugs:
        _validate_rel_endpoint_types(
            outgoing or {},
            incoming or {},
            slug_to_type,
        )

    return slug_to_type


# Write helpers (called inside db.transaction)

def _apply_names(slug: str, names: list[str]) -> None:
    db.cypher_query(PAGE_NAMES_UPDATE_QUERY, {'slug': slug, 'names': names})


def _apply_attrs(slug: str, raw_attrs: dict, entity_type: EntityType) -> None:
    db_attrs = normalize_patch_attributes(raw_attrs, entity_type)
    if db_attrs:
        db.cypher_query(
            PAGE_ATTRS_UPDATE_QUERY,
            {
                'slug': slug,
                "attrs": db_attrs
            }
        )


def _apply_article(slug: str, article: dict) -> None:
    db.cypher_query(
        PAGE_ARTICLE_UPSERT_QUERY,
        {
            'slug': slug,
            'text': article.get('text') or '',
            'image_url': article.get('image_url'),
        },
    )


def _apply_categories(slug: str, cat_slugs: list[str]) -> None:
    if cat_slugs:
        db.cypher_query(
            PAGE_CATEGORIES_REPLACE_QUERY,
            {
                'slug': slug,
                'cat_slugs': cat_slugs,
            },
        )
    else:
        db.cypher_query(PAGE_CATEGORIES_CLEAR_QUERY, {"slug": slug})


def _apply_outgoing_relations(slug: str, outgoing: dict) -> None:
    '''
    Replace outgoing edges of specified types.

    For each rel_type:
      1. Delete all (slug)-[:rel_type]->(*) edges.
      2. Create new (slug)-[:rel_type]->(target) edges for each item in the
         list.

    Two separate queries avoids the Cartesian product explosion.
    '''
    if not outgoing:
        # Explicit empty dict: wipe all outgoing :Page→:Page edges.
        db.cypher_query(PAGE_DELETE_ALL_OUTGOING_RELS_QUERY, {'slug': slug})
        return

    for rel_type, targets in outgoing.items():
        if rel_type not in ALLOWED_REL_TYPES:
            raise RuntimeError(
                f"rel_type '{rel_type}' not in ALLOWED_REL_TYPES. "
                "Validation must run before calling write helpers."
            )

        db.cypher_query(
            PAGE_RELS_OUTGOING_DELETE_TEMPLATE.format(rel_type=rel_type),
            {'slug': slug},
        )

        if targets:
            db.cypher_query(
                PAGE_RELS_OUTGOING_CREATE_TEMPLATE.format(rel_type=rel_type),
                {
                    'slug': slug,
                    'targets': [
                        {
                            'slug': t['slug'],
                            'properties': sanitize_rel_properties(
                                rel_type,
                                t.get('properties') or {}
                            )
                        }
                        for t in targets
                    ],
                },
            )


def _apply_incoming_relations(slug: str, incoming: dict) -> None:
    '''
    Replace incoming edges of specified types.

    For each rel_type:
      1. Delete all (*)-[:rel_type]->(slug) edges.
         This is scoped to edges that terminate at slug -
         it does NOT affect source nodes' other outgoing edges.
      2. Create new (source)-[:rel_type]->(slug) edges.
    '''
    if not incoming:
        # Explicit empty dict: wipe all incoming :Page→:Page edges.
        db.cypher_query(PAGE_DELETE_ALL_INCOMING_RELS_QUERY, {'slug': slug})
        return

    for rel_type, sources in incoming.items():
        if rel_type not in ALLOWED_REL_TYPES:
            raise RuntimeError(
                f"rel_type '{rel_type}' not in ALLOWED_REL_TYPES. "
                "Validation must run before calling write helpers."
            )

        db.cypher_query(
            PAGE_RELS_INCOMING_DELETE_TEMPLATE.format(rel_type=rel_type),
            {'slug': slug},
        )
        if sources:
            db.cypher_query(
                PAGE_RELS_INCOMING_CREATE_TEMPLATE.format(rel_type=rel_type),
                {
                    'slug': slug,
                    'sources': [
                        {
                            'slug': s['slug'],
                            'properties': sanitize_rel_properties(
                                rel_type,
                                s.get('properties') or {}
                            )
                        }
                        for s in sources
                    ],
                },
            )


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

    row = dict(zip(meta, results[0], strict=True))
    return _row_to_page_dict(row)


def update_page(
        slug: str,
        validated_data: dict,
        user_id: int | None = None,
) -> dict[str, Any]:
    '''
    Apply a partial update and return the refreshed page.

    Relations None-vs-{} semantics (enforced by _RelationDirectionField):
      - outgoing / incoming is None -> field was omitted -> no change
      - outgoing / incoming is {} -> explicitly empty -> delete all edges
                                                         in that direction
      - outgoing / incoming has keys -> per-type replacement
    '''

    results, _ = db.cypher_query(PAGE_FETCH_LABELS_QUERY, {'slug': slug})

    if not results:
        raise NotFound(
            detail=f'Page \'{slug}\' does not exist.',
            code='NOT_FOUND',
        )

    entity_type = labels_to_type(results[0][0]) or EntityType.CHARACTER

    # Extract relation sub-dicts
    raw_relations: dict = validated_data.get('relations') or {}
    outgoing: dict | None = raw_relations.get('outgoing')  # None if absent
    incoming: dict | None = raw_relations.get('incoming')  # None if absent
    categories: list | None = validated_data.get('categories')

    _preflight_relations(entity_type, outgoing, incoming)

    # Category existense
    if categories:
        _validate_category_slugs_exist(categories)

    # Write atomically
    with db.transaction:
        names: list | None = validated_data.get('names')
        if names is not None:
            _apply_names(slug, names)

        raw_attrs: dict = validated_data.get('attributes') or {}
        if raw_attrs:
            _apply_attrs(slug, raw_attrs, entity_type)

        article: dict | None = validated_data.get('article')
        if article is not None:
            _apply_article(slug, article)

        if categories is not None:
            _apply_categories(slug, categories)

        if outgoing is not None:
            _apply_outgoing_relations(slug, outgoing)
        if incoming is not None:
            _apply_incoming_relations(slug, incoming)

    # Re-fetch after commit to return the canonical representation
    return get_page(slug, user_id=user_id)


def create_page(
    node_labels: str,
    slug: str,
    names: list[str],
    attrs: dict,
    article: dict | None = None,
    categories: list[str] | None = None,
    relations: dict | None = None,
    entity_type: EntityType = EntityType.CHARACTER,
    user_id: int | None = None,
) -> dict[str, Any]:
    '''
    Atomically create a new page node with optional article, categories,
    and relations in a single transaction.

    All pre-flight validation happens BEFORE the transaction is opened so
    that bad input surfaces as a 4xx without any partial write.

    `node_labels` must come from EntityConfig.node_labels (hardcoded string,
    never from user input).
    `attrs` must already be normalised via normalize_patch_attributes before
    calling this function.
    '''
    raw_relations = relations or {}
    outgoing: dict | None = raw_relations.get('outgoing')
    incoming: dict | None = raw_relations.get('incoming')

    _preflight_relations(entity_type, outgoing, incoming)

    if categories:
        _validate_category_slugs_exist(categories)

    with db.transaction:
        db.cypher_query(
            _CREATE_NODE_TEMPLATE.format(node_labels=node_labels),
            {
                'slug': slug,
                'names': names,
                'attrs': attrs,
            }
        )

        if article is not None:
            _apply_article(slug, article)

        if categories is not None:
            _apply_categories(slug, categories)

        if outgoing is not None:
            _apply_outgoing_relations(slug, outgoing)
        if incoming is not None:
            _apply_incoming_relations(slug, incoming)

    # Re-fetch after commit
    return get_page(slug, user_id=user_id)


def delete_page(slug: str) -> None:
    '''
    Delete a page ode, its article node, and all edges.

    DETACH DELETE removes all edges from/to the page.
    The article node is explicitly deleted to avoid orphaned nodes (it has no
    :Page label so it would not be found by any MATCH on :Page)
    '''

    results, _ = db.cypher_query(PAGE_DELETE_QUERY, {'slug': slug})
    if not results:
        raise NotFound(
            detail=f'Page \'{slug}\' does not exists.',
            code='NOT_FOUND',
        )


def _execute_like_query(
        query: str,
        slug: str,
        user_id: int,
) -> dict[str, Any]:
    '''
    Run a like/inlike query and return the response dict.

    Both PAGE_LIKE_ADD_QUERY and PAGE_LIKE_REMOVE_QUERY start with
    MATCH (p:Page {slug: $slug}), so they naturally return 0 rows if the
    page does not exist - no separate existence check needed.
    '''
    results, meta = db.cypher_query(
        query,
        {
            'slug': slug,
            'user_id': user_id
        }
    )
    if not results:
        raise NotFound(
            detail=f'Page \'{slug}\' does not exist.',
            code='NOT_FOUND'
        )

    row = dict(zip(meta, results[0]))
    return {
        'likes_count': row['likes_count'],
        'is_liked': row['is_liked'],
    }


def like_page(slug: str, user_id: int) -> dict[str, Any]:
    '''
    Idempotently like a page.

    Creates the :User node (UserRef) if it does not exists yet.
    '''

    return _execute_like_query(PAGE_LIKE_ADD_QUERY, slug, user_id)


def unlike_page(slug: str, user_id: int) -> dict[str, Any]:
    '''
    Idempotently unlike a page.

    If the user never liked the page, OPTIONAL MATCH finds nothing.
    '''
    return _execute_like_query(PAGE_LIKE_REMOVE_QUERY, slug, user_id)
