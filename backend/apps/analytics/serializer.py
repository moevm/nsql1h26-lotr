"""
Serializers for the analytics app.

These are read-only output serializers used by drf-spectacular for OpenAPI
schema generation.  The actual data is assembled as plain dicts in services.py
and returned directly - DRF serializes them without a model binding.
"""

from rest_framework import serializers


# Global stats endpoint

class _CountsSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    characters = serializers.IntegerField()
    races = serializers.IntegerField()
    locations = serializers.IntegerField()
    events = serializers.IntegerField()
    organizations = serializers.IntegerField()
    timelines = serializers.IntegerField()
    items = serializers.IntegerField()
    languages = serializers.IntegerField()
    scripts = serializers.IntegerField()


class _CharacterByRaceSerializer(serializers.Serializer):
    slug = serializers.CharField()
    name = serializers.CharField()
    count = serializers.IntegerField()


class _CharacterByGenderSerializer(serializers.Serializer):
    gender = serializers.CharField()
    count = serializers.IntegerField()


class _IsAliveStatsSerializer(serializers.Serializer):
    alive = serializers.IntegerField()
    deceased = serializers.IntegerField()


class _EventByTimelineSerializer(serializers.Serializer):
    timeline_slug = serializers.CharField()
    name = serializers.CharField()
    count = serializers.IntegerField()


class _TypeCountSerializer(serializers.Serializer):
    type = serializers.CharField()
    count = serializers.IntegerField()


class _TopConnectedItemSerializer(serializers.Serializer):
    slug = serializers.CharField()
    name = serializers.CharField()
    connections_count = serializers.IntegerField()


class _TopConnectedSerializer(serializers.Serializer):
    characters = _TopConnectedItemSerializer(many=True)
    races = _TopConnectedItemSerializer(many=True)
    locations = _TopConnectedItemSerializer(many=True)
    events = _TopConnectedItemSerializer(many=True)
    organizations = _TopConnectedItemSerializer(many=True)
    items = _TopConnectedItemSerializer(many=True)
    timelines = _TopConnectedItemSerializer(many=True)
    languages = _TopConnectedItemSerializer(many=True)
    scripts = _TopConnectedItemSerializer(many=True)


class _PageEngagementSerializer(serializers.Serializer):
    slug = serializers.CharField()
    name = serializers.CharField()
    type = serializers.CharField(
        help_text='Entity type derived from the Neo4j node label (e.g. "character").'
    )
    count = serializers.IntegerField()


class GlobalStatsSerializer(serializers.Serializer):
    """Read-only response shape for GET /analytics/global/."""

    counts = _CountsSerializer()
    characters_by_race = _CharacterByRaceSerializer(many=True)
    characters_by_gender = _CharacterByGenderSerializer(many=True)
    is_alive_stats = _IsAliveStatsSerializer()
    events_by_timeline = _EventByTimelineSerializer(many=True)
    locations_by_type = _TypeCountSerializer(many=True)
    items_by_type = _TypeCountSerializer(many=True)
    top_connected = _TopConnectedSerializer()
    most_liked = _PageEngagementSerializer(many=True)
    most_commented = _PageEngagementSerializer(many=True)


# Neighbors endpoint

class _PageSummarySerializer(serializers.Serializer):
    '''Minimal page representation used in neighbors root and node lists.'''

    slug = serializers.CharField()
    type = serializers.CharField(
        help_text='Entity type derived from the Neo4j label (e.g. "character).'
    )
    name = serializers.CharField(allow_null=True)
    image_url = serializers.CharField(allow_null=True)


class _NeighborEdgeSerializer(serializers.Serializer):
    '''
    A directed lore edge between two nodes in the neighbor subgraph.

    `from` and `to` are Python keywords;
    DRF does not allow them as class-level attribute names.
    The standard workaround is to declare the fields via
    `_declared_fields` after class definition so the metaclass
    never sees the bare name ``from``.
    '''
    type = serializers.CharField(help_text='Relationship type, e.g. OF_RACE.')
    properties = serializers.DictField(
        child=serializers.JSONField(),
        allow_empty=True,
        help_text='Edge properties (e.g. role, fromDate) — empty dict when none.',
    )


# Monkey-patch "from" and "to" fields after class creation to avoid the
# SyntaxError that would result from using reserved keywords as class attrs.
_NeighborEdgeSerializer._declared_fields['from'] = serializers.CharField(
    help_text='Slug of the source node.'
)
_NeighborEdgeSerializer._declared_fields['to'] = serializers.CharField(
    help_text='Slug of the target node.'
)


class _NeighborStatsSerializer(serializers.Serializer):
    total_neighbors = serializers.IntegerField(
        help_text='Number of neighbour nodes returned (respects limit and filters).'
    )
    by_type = serializers.DictField(
        child=serializers.IntegerField(),
        help_text='Count of neighbour nodes per entity type.',
    )
    by_relation = serializers.DictField(
        child=serializers.IntegerField(),
        help_text='Count of edges per relationship type.',
    )


class NeighborsResponseSerializer(serializers.Serializer):
    '''Read-only reponse shape for GET /analytics/neighbors/.'''

    root_node = _PageSummarySerializer(help_text='The queried page.')
    nodes = _PageSummarySerializer(
        many=True,
        help_text='Neighbor nodes reachable within the requested depth.'
    )
    edges = _NeighborEdgeSerializer(
        many=True,
        help_text=(
            'Induced subgraph: all directed lore edges whose both endpoints '
            'are present in root + nodes.'
        ),
    )
    stats = _NeighborStatsSerializer()
