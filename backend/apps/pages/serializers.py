'''
Serializers for the pages app.

Only INPUT serializers live here - the PATCH request body.
GET response is built as a plain dict in services.py:
  - the response shape is a discriminated union (depends on entity type)
  - DRF serializers don't model discriminated unions cleanly without
    significant boilerplate, and the service already validates the data.

PATCH /pages/{slug}/ accepts any subset of:
  - names - replaces the names list
  - attributes - partial update of type-specific fields
  - article - upsert the article node
  - categories - replaces the full category list (list of slugs)
  - relations - replaces rels per type (see PageRelationsField)

The @extend_schema in views.py documents the GET response shape for Swagger
using inline_serializer so API clients still get a useful schema.
'''

from rest_framework import serializers


class ArticleUpdateSerializer(serializers.Serializer):
    '''Inline article upsert inside PATCH /pages/{slug}'''

    text = serializers.CharField(allow_blank=True, required=False, default='')
    image_url = serializers.URLField(
        allow_null=True, required=False, default=None
    )


class RelationItemSerializer(serializers.Serializer):
    '''
    One edge endpoint in a PATCH relations list

    `slug` refers to the other page involved in the edge.
    For outgoing edges: slug is the target (edge points FROM current page
    TO slug).
    For incoming edges: slug is the source (edge points FROM slug
    TO current page).

    `properties` carries edge attributes (role, fromDate, toDate, etc.).
    Uses plain DictField without child-type restriction because edge property
    values are heterogeneous (strings, nulls, possibly other JSON types).
    '''

    slug = serializers.SlugField(max_length=80)
    properties = serializers.DictField(required=False, default=dict)


class _RelationDirectionField(serializers.DictField):
    '''
    Validates one direction (outgoing OR incoming) of the relations map.

    Expected shape:
        {
            "MEMBER_OF": [{"slug": "bibonki", "properties": {"role": "..."}}],
            "OWNS": []
        }

    Value semantics (after deserialization):
        None / field absent -> "do not touch this direction" (no-op)
        {} (explicit empty dict) -> "delete ALL edges in this direction"
        {"MEMBER_OF": [...]} -> "replace MEMBER_OF edges; others unchanged"
        {"MEMBER_OF": []} -> "delete all MEMBER_OF edges; others unchanged"

    Keys are relationship type strings,
    values are lists of RelationItemSerializer.
    An empty list means "delete all edges of this type in this direction".
    The whitelist check (ALLOWED_REL_TYPES) is done in services.py, not here,
#   because it depends on the entity type and we want one error format.
    '''

    def __init__(self, **kwargs: object) -> None:
        # allow_null=True so that an explicit JSON null means "no-op" (same as
        # omitting the field).  The default=None lets us distinguish "user sent
        # outgoing: {}" (empty dict -> delete all) from "user omitted outgoing"
        # (None -> no-op).
        kwargs.setdefault('allow_null', True)
        kwargs.setdefault('default', None)
        super().__init__(**kwargs)  # type: ignore

    def to_internal_value(self, data: dict) -> dict:
        # if data is None:
        #     return None  # type: ignore[return-value]

        if not isinstance(data, dict):
            raise serializers.ValidationError('Must be an object.')

        result: dict = {}
        for rel_type, items in data.items():
            if not isinstance(items, list):
                raise serializers.ValidationError(
                    {rel_type: ['Must be a list of edge endpoint objects.']}
                )

            validated: list = []
            for i, target in enumerate(items):
                s = RelationItemSerializer(data=target)

                if not s.is_valid():
                    raise serializers.ValidationError(
                        {rel_type: {i: s.errors}}
                    )
                validated.append(s.validated_data)

            result[rel_type] = validated

        return result


class PageRelationsSerializer(serializers.Serializer):
    '''
    Validates the `relations` object in PATCH /pages/{slug}/.

    Mirrors the GET response structure so the frontend can round-trip
    the value without transformation.

    The only difference from GET is that the endpoint summary objects
    ({slug, type, name, imageUrl}) are replaced by plain {"slug": "..."} -
    the backend only needs the slug to identify the other node.
    '''
    outgoing = _RelationDirectionField(required=False)
    incoming = _RelationDirectionField(required=False)


class PageUpdateSerializer(serializers.Serializer):
    '''
    Input serializer for PATCH /pages/{slug}

    All fields are optional.
    At least one must be provided (validated in view).
    '''

    names = serializers.ListField(
        child=serializers.CharField(max_length=100),
        min_length=1,
        required=False,
    )

    # DictField with no child restriction: attribute shapes vary per entity
    # type. Type-specific validation and DB-name mapping happen in services.py.
    attributes = serializers.DictField(required=False)

    article = ArticleUpdateSerializer(required=False)

    categories = serializers.ListField(
        child=serializers.SlugField(max_length=80),
        required=False,
    )

    relations = PageRelationsSerializer(required=False)

    def validate(self, attrs: dict) -> dict:
        '''Require at least one field to be present'''
        if not attrs:
            raise serializers.ValidationError(
                'At least one field must be provided in a PATCH request.'
            )

        return attrs


class PageCreateSerializer(PageUpdateSerializer):
    '''
    Input serializer for POST /{catalog}/ (character, race, location, etc.)

    Extends PageUpdateSerializer with:
      - slug: required (the new page's public identifier)
      - names: required (at least one name is mandatory)
      - attributes, article, categories, relations: all optional, same as PATCH

    The entity type is implicit from the endpoint, not in the body.
    '''

    slug = serializers.SlugField(max_length=80, required=True)

    names = serializers.ListField(
        child=serializers.CharField(max_length=100),
        min_length=1,
        required=True,
    )

    def validate(self, attrs: dict) -> dict:
        # slug and names are always present.
        # no "at least one field" guard needed.
        return attrs
