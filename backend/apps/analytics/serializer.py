"""
Serializers for the analytics app.

These are read-only output serializers used by drf-spectacular for OpenAPI
schema generation.  The actual data is assembled as plain dicts in services.py
and returned directly - DRF serializes them without a model binding.
"""

from rest_framework import serializers


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
