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
'''

from rest_framework import serializers


class ArticleUpdateSerializer(serializers.Serializer):
    '''Inline article upsert inside PATCH /pages/{slug}'''

    text = serializers.CharField(allow_blank=True, required=False, default='')
    imageUrl = serializers.URLField(
        allow_null=True, required=False, default=None
    )


class RelationTargetSerializer(serializers.Serializer):
    '''
    One target in a relation list.
    `properties` carries edge attributes (role, fromDate, etc.).
    '''

    slug = serializers.SlugField(max_length=80)
    properties = serializers.DictField(
        child=serializers.CharField(allow_null=True),
        required=False,
        default=dict,
    )


class PageRelationField(serializers.DictField):
    '''
    Validate the `relations` map sent in PATCH.

    Expected shape:
    {
        "MEMBER_OF": [
            {"slug": "fellowship-of-the-ring", "properties": {"role": "Ring-bearer"}}
        ],
        "OWNS": []   // empty list = delete all OWNS relations
    }

    Keys are relationship type strings,
    values are lists of RelationTargetSerializer.
    The whitelist check (ALLOWED_REL_TYPES) is done in services.py, not here,
    because it depends on the entity type and we want one error format.
    '''

    def to_internal_value(self, data: dict) -> dict:
        if not isinstance(data, dict):
            raise serializers.ValidationError('Must be an object.')

        result: dict = {}
        for rel_type, targets in data.items():
            if not isinstance(targets, list):
                raise serializers.ValidationError(
                    {rel_type: ['Must be a list of target objects.']}
                )

            validated_targets = []
            for i, target in enumerate(targets):
                s = RelationTargetSerializer(data=target)

                if not s.is_valid():
                    raise serializers.ValidationError(
                        {rel_type: {i: s.errors}}
                    )
                validated_targets.append(s.validated_data)

            result[rel_type] = validated_targets

        return result


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

    relations = PageRelationField(required=False)

    def validate(self, attrs: dict) -> dict:
        '''Require at least one field to be present'''
        if not attrs:
            raise serializers.ValidationError(
                'At least one field must be provided in a PATCH request.'
            )

        return attrs
