"""
Output serializers for catalog list endpoints (GET /characters/, etc.)

These describe the flat row shape returned by the catalog Cypher queries.
They are used exclusively for GET list responses; POST now uses
PageCreateSerializer from apps.pages.serializers and returns the full
page representation (same as GET /pages/{slug}/).
"""


from rest_framework import serializers


class BaseCatalogSerializer(serializers.Serializer):
    '''
    Shared base for all catalog list output serializers.

    Provides: slug, names, name ( = names[0]).
    Subclasses add type-specific fields.
    '''

    slug = serializers.CharField()
    names = serializers.ListField(child=serializers.CharField(), allow_null=True)
    name = serializers.SerializerMethodField()

    def get_name(self, obj: dict) -> str | None:
        names: list[str] = obj.get('names') or []
        return names[0] if names else None



class CharacterOutputSerializer(BaseCatalogSerializer):
    '''Output of one character in a catalog list'''

    name = serializers.SerializerMethodField()
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


class RaceOutputSerializer(BaseCatalogSerializer):
    lifespan = serializers.CharField(allow_null=True)
    avg_height = serializers.CharField(allow_null=True)
    hair = serializers.CharField(allow_null=True)
    eyes = serializers.CharField(allow_null=True)
    skin = serializers.CharField(allow_null=True)
    weaponry = serializers.CharField(allow_null=True)
    clothing = serializers.CharField(allow_null=True)
    distinctions = serializers.CharField(allow_null=True)


class LocationOutputSerializer(BaseCatalogSerializer):
    entity_type = serializers.CharField(allow_null=True)
    population = serializers.CharField(allow_null=True)
    creation_date = serializers.CharField(allow_null=True)
    destruction_date = serializers.CharField(allow_null=True)
    notable_for = serializers.CharField(allow_null=True)


class EventOutputSerializer(BaseCatalogSerializer):
    entity_type = serializers.CharField(allow_null=True)
    start_date = serializers.CharField(allow_null=True)
    end_date = serializers.CharField(allow_null=True)
    casualties = serializers.CharField(allow_null=True)
    notable_for = serializers.CharField(allow_null=True)


class OrganizationOutputSerializer(BaseCatalogSerializer):
    entity_type = serializers.CharField(allow_null=True)
    founded_date = serializers.CharField(allow_null=True)
    dissolved_date = serializers.CharField(allow_null=True)
    clothing = serializers.CharField(allow_null=True)
    weaponry = serializers.CharField(allow_null=True)
    purpose = serializers.CharField(allow_null=True)
    notable_for = serializers.CharField(allow_null=True)


class TimelineOutputSerializer(BaseCatalogSerializer):
    start_date = serializers.CharField(allow_null=True)
    end_date = serializers.CharField(allow_null=True)
    abbreviation = serializers.CharField(allow_null=True)


class ItemOutputSerializer(BaseCatalogSerializer):
    entity_type = serializers.CharField(allow_null=True)
    material = serializers.CharField(allow_null=True)
    notable_for = serializers.CharField(allow_null=True)

class LanguageOutputSerializer(BaseCatalogSerializer):
    family = serializers.CharField(allow_null=True)


class ScriptOutputSerializer(BaseCatalogSerializer):
    pass


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
