from rest_framework import serializers


class _NamesField(serializers.ListField):
    '''names: LIST<STRING>, at least one value'''

    child = serializers.CharField(max_length=100)

    def __init__(self, **kwargs) -> None:
        kwargs.setdefault('min_length', 1)
        super().__init__(**kwargs)


class _OptionalNamesField(serializers.ListField):
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


class CharacterCreateSerializer(serializers.Serializer):
    '''Entrypoint fir POST /characters/'''

    slug = serializers.SlugField(max_length=80, required=True)
    names = _NamesField()
    titles = _OptionalNamesField()
    gender = serializers.ChoiceField(
        choices=['Male', 'Female', 'Unknown'],
        allow_null=True,
        required=False,
        default=None
    )
    birth_date = serializers.CharField(
        max_length=30, allow_null=True, required=False, default=None
    )
    death_date = serializers.CharField(
        max_length=30, allow_null=True, required=False, default=None
    )
    hair = serializers.CharField(
        max_length=60, allow_null=True, required=False, default=None
    )
    eyes = serializers.CharField(
        max_length=60, allow_null=True, required=False, default=None
    )
    height = serializers.CharField(
        max_length=30, allow_null=True, required=False, default=None
    )
    weapon = serializers.CharField(
        max_length=80, allow_null=True, required=False, default=None
    )
    clothing = serializers.CharField(
        max_length=80, allow_null=True, required=False, default=None
    )
    notable_for = serializers.CharField(
        max_length=300, allow_null=True, required=False, default=None
    )


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


class RaceCreateSerializer(serializers.Serializer):
    slug = serializers.SlugField(max_length=80, required=True)
    names = _NamesField()
    lifespan = serializers.CharField(
        max_length=60, allow_null=True, required=False, default=None
    )
    avg_height = serializers.CharField(
        max_length=30, allow_null=True, required=False, default=None
    )
    hair = serializers.CharField(
        max_length=60, allow_null=True, required=False, default=None
    )
    eyes = serializers.CharField(
        max_length=60, allow_null=True, required=False, default=None
    )
    skin = serializers.CharField(
        max_length=60, allow_null=True, required=False, default=None
    )
    weaponry = serializers.CharField(
        max_length=100, allow_null=True, required=False, default=None
    )
    clothing = serializers.CharField(
        max_length=100, allow_null=True, required=False, default=None
    )
    distinctions = serializers.CharField(
        max_length=300, allow_null=True, required=False, default=None
    )


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


class LocationCreateSerializer(serializers.Serializer):
    slug = serializers.SlugField(max_length=80, required=True)
    names = _NamesField()
    entity_type = serializers.CharField(
        max_length=60, allow_null=True, required=False, default=None
    )
    population = serializers.CharField(
        max_length=200, allow_null=True, required=False, default=None
    )
    creation_date = serializers.CharField(
        max_length=30, allow_null=True, required=False, default=None
    )
    destruction_date = serializers.CharField(
        max_length=30, allow_null=True, required=False, default=None
    )
    notable_for = serializers.CharField(
        max_length=300, allow_null=True, required=False, default=None
    )


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


class EventCreateSerializer(serializers.Serializer):
    slug = serializers.SlugField(max_length=80, required=True)
    names = _NamesField()
    entity_type = serializers.CharField(
        max_length=60, allow_null=True, required=False, default=None
    )
    start_date = serializers.CharField(
        max_length=30, allow_null=True, required=False, default=None
    )
    end_date = serializers.CharField(
        max_length=30, allow_null=True, required=False, default=None
    )
    casualties = serializers.CharField(
        max_length=200, allow_null=True, required=False, default=None
    )
    notable_for = serializers.CharField(
        max_length=300, allow_null=True, required=False, default=None
    )


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


class OrganizationCreateSerializer(serializers.Serializer):
    slug = serializers.SlugField(max_length=80, required=True)
    names = _NamesField()
    entity_type = serializers.CharField(
        max_length=60, allow_null=True, required=False, default=None
    )
    founded_date = serializers.CharField(
        max_length=30, allow_null=True, required=False, default=None
    )
    dissolved_date = serializers.CharField(
        max_length=30, allow_null=True, required=False, default=None
    )
    clothing = serializers.CharField(
        max_length=100, allow_null=True, required=False, default=None
    )
    weaponry = serializers.CharField(
        max_length=100, allow_null=True, required=False, default=None
    )
    purpose = serializers.CharField(
        max_length=300, allow_null=True, required=False, default=None
    )
    notable_for = serializers.CharField(
        max_length=300, allow_null=True, required=False, default=None
    )


class TimelineOutputSerializer(serializers.Serializer):
    slug = serializers.CharField()
    names = serializers.ListField(
        child=serializers.CharField(), allow_null=True
    )
    start_date = serializers.CharField(allow_null=True)
    end_date = serializers.CharField(allow_null=True)
    abbreviation = serializers.CharField(allow_null=True)


class TimelineCreateSerializer(serializers.Serializer):
    slug = serializers.SlugField(max_length=80, required=True)
    name = _NamesField()
    start_date = serializers.CharField(
        max_length=30, allow_null=True, required=False, default=None
    )
    end_date = serializers.CharField(
        max_length=30, allow_null=True, required=False, default=None
    )
    abbreviation = serializers.CharField(
        max_length=10, allow_null=True, required=False, default=None
    )


class ItemOutputSerializer(serializers.Serializer):
    slug = serializers.CharField()
    names = serializers.ListField(
        child=serializers.CharField(), allow_null=True
    )
    entity_type = serializers.CharField(allow_null=True)
    material = serializers.CharField(allow_null=True)
    notable_for = serializers.CharField(allow_null=True)


class ItemCreateSerializer(serializers.Serializer):
    slug = serializers.SlugField(max_length=80, required=True)
    names = _NamesField()
    entity_type = serializers.CharField(
        max_length=60, allow_null=True, required=False, default=None
    )
    material = serializers.CharField(
        max_length=100, allow_null=True, required=False, default=None
    )
    notable_for = serializers.CharField(
        max_length=300, allow_null=True, required=False, default=None
    )


class LanguageOutputSerializer(serializers.Serializer):
    slug = serializers.CharField()
    names = serializers.ListField(
        child=serializers.CharField(), allow_null=True
    )
    family = serializers.CharField(allow_null=True)


class LanguageCreateSerializer(serializers.Serializer):
    slug = serializers.SlugField(max_length=80, required=True)
    names = _NamesField()
    family = serializers.CharField(
        max_length=80, allow_null=True, required=False, default=None
    )


class ScriptOutputSerializer(serializers.Serializer):
    slug = serializers.CharField()
    names = serializers.ListField(
        child=serializers.CharField(), allow_null=True
    )


class ScriptCreateSerializer(serializers.Serializer):
    slug = serializers.SlugField(max_length=80, required=True)
    names = _NamesField()


# Pagination wrapper
class PaginatedResponseSerializer(serializers.Serializer):
    '''
    Wrapper for {count, next, previous, results}.
    Used in @extend_schema in views.
    '''

    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = serializers.ListField()
