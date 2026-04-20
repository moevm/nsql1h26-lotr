"""
Output serializers for catalog list endpoints (GET /characters/, etc.)

These describe the flat row shape returned by the catalog Cypher queries.
They are used exclusively for GET list responses; POST now uses
PageCreateSerializer from apps.pages.serializers and returns the full
page representation (same as GET /pages/{slug}/).
"""


from rest_framework import serializers


class _NamesField(serializers.ListField):
    '''names: LIST<STRING>, at least one value'''

    child = serializers.CharField(max_length=100)

    def __init__(self, **kwargs) -> None:
        kwargs.setdefault('min_length', 1)
        super().__init__(**kwargs)


class _OptionalNamesField(serializers.ListField):
    '''Optional LIST<STRING>, defaults to empty list'''

    child = serializers.CharField(max_length=100)

    def __init__(self, **kwargs) -> None:
        kwargs.setdefault('required', False)
        kwargs.setdefault('allow_null', True)
        kwargs.setdefault('default', list)
        super().__init__(**kwargs)


class CharacterOutputSerializer(serializers.Serializer):
    '''Output of one character in a catalog list'''
    slug = serializers.CharField()
    names = serializers.ListField(
        child=serializers.CharField(), allow_null=True
    )
    titles = serializers.ListField(
        child=serializers.CharField(), allow_null=True
    )
    gender = serializers.CharField(allow_null=True)
    birth_date = serializers.CharField(allow_null=True)
    death_date = serializers.CharField(allow_null=True)
    hair = serializers.CharField(allow_null=True)
    eyes = serializers.CharField(allow_null=True)
    height = serializers.CharField(allow_null=True)
    weapon = serializers.CharField(allow_null=True)
    clothing = serializers.CharField(allow_null=True)
    notable_for = serializers.CharField(allow_null=True)

    race_slug = serializers.CharField(allow_null=True)
    race_name = serializers.CharField(allow_null=True)

    born_in_slug = serializers.CharField(allow_null=True)
    born_in_name = serializers.CharField(allow_null=True)


class RaceOutputSerializer(serializers.Serializer):
    slug = serializers.CharField()
    names = serializers.ListField(
        child=serializers.CharField(), allow_null=True
    )
    lifespan = serializers.CharField(allow_null=True)
    avg_height = serializers.CharField(allow_null=True)
    hair = serializers.CharField(allow_null=True)
    eyes = serializers.CharField(allow_null=True)
    skin = serializers.CharField(allow_null=True)
    weaponry = serializers.CharField(allow_null=True)
    clothing = serializers.CharField(allow_null=True)
    distinctions = serializers.CharField(allow_null=True)


class LocationOutputSerializer(serializers.Serializer):
    slug = serializers.CharField()
    names = serializers.ListField(
        child=serializers.CharField(), allow_null=True
    )
    entity_type = serializers.CharField(allow_null=True)
    population = serializers.CharField(allow_null=True)
    creation_date = serializers.CharField(allow_null=True)
    destruction_date = serializers.CharField(allow_null=True)
    notable_for = serializers.CharField(allow_null=True)


class EventOutputSerializer(serializers.Serializer):
    slug = serializers.CharField()
    names = serializers.ListField(
        child=serializers.CharField(), allow_null=True
    )
    entity_type = serializers.CharField(allow_null=True)
    start_date = serializers.CharField(allow_null=True)
    end_date = serializers.CharField(allow_null=True)
    casualties = serializers.CharField(allow_null=True)
    notable_for = serializers.CharField(allow_null=True)


class OrganizationOutputSerializer(serializers.Serializer):
    slug = serializers.CharField()
    names = serializers.ListField(
        child=serializers.CharField(), allow_null=True
    )
    entity_type = serializers.CharField(allow_null=True)
    founded_date = serializers.CharField(allow_null=True)
    dissolved_date = serializers.CharField(allow_null=True)
    clothing = serializers.CharField(allow_null=True)
    weaponry = serializers.CharField(allow_null=True)
    purpose = serializers.CharField(allow_null=True)
    notable_for = serializers.CharField(allow_null=True)


class TimelineOutputSerializer(serializers.Serializer):
    slug = serializers.CharField()
    names = serializers.ListField(
        child=serializers.CharField(), allow_null=True
    )
    start_date = serializers.CharField(allow_null=True)
    end_date = serializers.CharField(allow_null=True)
    abbreviation = serializers.CharField(allow_null=True)


class ItemOutputSerializer(serializers.Serializer):
    slug = serializers.CharField()
    names = serializers.ListField(
        child=serializers.CharField(), allow_null=True
    )
    entity_type = serializers.CharField(allow_null=True)
    material = serializers.CharField(allow_null=True)
    notable_for = serializers.CharField(allow_null=True)


class LanguageOutputSerializer(serializers.Serializer):
    slug = serializers.CharField()
    names = serializers.ListField(
        child=serializers.CharField(), allow_null=True
    )
    family = serializers.CharField(allow_null=True)


class ScriptOutputSerializer(serializers.Serializer):
    slug = serializers.CharField()
    names = serializers.ListField(
        child=serializers.CharField(), allow_null=True
    )


# Pagination envelope - used in @extend_schema
class PaginatedResponseSerializer(serializers.Serializer):
    '''
    Wrapper for {count, next, previous, results}.
    Used in @extend_schema in views.
    '''

    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = serializers.ListField()
