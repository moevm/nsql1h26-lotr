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
    never sees the bare name `from`.
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


class _PathEdgeSerializer(serializers.Serializer):
    '''Edge between two consecutive nodes in the shortest path.'''

    type = serializers.CharField(help_text='Relationship type, e.g. OF_RACE')
    properties = serializers.DictField(
        child=serializers.JSONField(),
        allow_empty=True,
        help_text='Edge properties as stored in Neo4j (empty dict when none).'
    )


class _PathStepSerializer(serializers.Serializer):
    '''One step in the ordered shortest path chain.'''

    node = _PageSummarySerializer(help_text='The page at this step.')
    edge_to_next = _PathEdgeSerializer(
        allow_null=True,
        help_text=(
            'Edge leading to the next step.  Null for the last node in the path.'
        ),
    )


class ShortestPathResponseSerializer(serializers.Serializer):
    '''
    Read-only reponse shape for GET /analytics/shortest-path/.

    `from` and `to` are Python reserved keywords; they are declared via
    `_declared_fields` after class creation to avoid a SyntaxError.
    '''

    found = serializers.BooleanField(
        help_text='True if a path was found within max_depth hops.'
    )
    length = serializers.IntegerField(
        allow_null=True,
        help_text='Number of hops in the shortest path; null when found=False'
    )
    path = _PathStepSerializer(
        many=True,
        help_text=(
            'Ordered chain of path steps from start to end node. '
            'Empty list when found=false.'
        ),
    )


ShortestPathResponseSerializer._declared_fields['from'] = _PageSummarySerializer(
    help_text='PageSummary of the start node (always present, even when found=false).'
)
ShortestPathResponseSerializer._declared_fields['to'] = _PageSummarySerializer(
    help_text='PageSummary of the end node (always present, even when found=false).'
)


class _SimpleDataPointSerializer(serializers.Serializer):
    x = serializers.CharField(help_text='X-axis bucket label.')
    value = serializers.IntegerField(help_text='Count of entities in this bucket.')


class CustomAnalyticsSimpleSerializer(serializers.Serializer):
    '''
    Response shape for GET /analytics/custom/ without group_by.
    '''

    entity_type = serializers.CharField()
    attr = serializers.CharField()
    group_by = serializers.CharField(
        allow_null=True,
        help_text='Always null for the simple (non-grouped) response.',
    )


CustomAnalyticsSimpleSerializer._declared_fields['data'] = _SimpleDataPointSerializer(
    many=True,
    help_text='X-axis buckets ordered by count descending.',
)


class CustomAnalyticsGroupedSerializer(serializers.Serializer):
    '''
    Response shape for GET /analytics/custom/ with group_by.
    '''

    entity_type = serializers.CharField()
    attr = serializers.CharField()
    group_by = serializers.CharField(help_text='The secondary grouping attribute name.')
    groups = serializers.ListField(
        child=serializers.CharField(),
        help_text='Sorted list of all group values present in data rows.',
    )


CustomAnalyticsGroupedSerializer._declared_fields['data'] = serializers.ListField(
        child=serializers.DictField(
            child=serializers.JSONField(),
        ),
        help_text=(
            'Stacked-bar rows.  Each row contains `x` (string) plus one integer '
            'key per entry in `groups`.  Rows are ordered by total count descending, '
            'capped at `top_n`.'
        ),
    )
