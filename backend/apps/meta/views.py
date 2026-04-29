from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

NODE_TYPES = [
    {"type": "character", "label": "Character", "pluralLabel": "Characters"},
    {"type": "race", "label": "Race", "pluralLabel": "Races"},
    {"type": "location", "label": "Location", "pluralLabel": "Locations"},
    {"type": "event", "label": "Event", "pluralLabel": "Events"},
    {"type": "organization", "label": "Organization", "pluralLabel": "Organizations"},
    {"type": "timeline", "label": "Timeline", "pluralLabel": "Timelines"},
    {"type": "item", "label": "Item", "pluralLabel": "Items"},
    {"type": "language", "label": "Language", "pluralLabel": "Languages"},
    {"type": "script", "label": "Script", "pluralLabel": "Scripts"},
]

# TO DO: check types
RELATION_TYPES = [
    {"type": "CHILD_OF", "label": "Child of", "from": ["character"], "to": ["character"]},
    {"type": "MARRIED_TO", "label": "Married to", "from": ["character"], "to": ["character"]},
    {"type": "SIBLING_OF", "label": "Sibling of", "from": ["character"], "to": ["character"]},
    {"type": "OF_RACE", "label": "Of race", "from": ["character"], "to": ["race"]},
    {"type": "BORN_IN", "label": "Born in", "from": ["character"], "to": ["location"]},
    {"type": "DIED_IN", "label": "Died in", "from": ["character"], "to": ["location"]},
    {"type": "DWELLED_IN", "label": "Dwelled in", "from": ["character"], "to": ["location"]},
    {"type": "SPEAKS", "label": "Speaks", "from": ["character"], "to": ["language"]},
    {"type": "MEMBER_OF", "label": "Member of", "from": ["character"], "to": ["organization"]},
    {"type": "PARTICIPATED_IN", "label": "Participated in", "from": ["character"], "to": ["event"]},
    {"type": "LIVED_DURING", "label": "Lived during", "from": ["character"], "to": ["timeline"]},
    {"type": "RULED", "label": "Ruled", "from": ["character"], "to": ["location", "race"]},
    {"type": "WIELDS", "label": "Wields", "from": ["character"], "to": ["item"]},
    {"type": "OWNS", "label": "Owns", "from": ["character"], "to": ["item"]},
    {"type": "BORE", "label": "Bore", "from": ["character"], "to": ["item"]},
    {"type": "CRAFTED", "label": "Crafted", "from": ["character"], "to": ["item"]},
    {"type": "SUBRACE_OF", "label": "Subrace of", "from": ["race"], "to": ["race"]},
    {"type": "INHABITS", "label": "Inhabits", "from": ["race"], "to": ["location"]},
    {"type": "REGION_OF", "label": "Region of", "from": ["location"], "to": ["location"]},
    {"type": "TOOK_PLACE_IN", "label": "Took place in", "from": ["event"], "to": ["location"]},
    {"type": "PART_OF", "label": "Part of", "from": ["event"], "to": ["event"]},
    {"type": "OCCURRED_DURING", "label": "Occurred during", "from": ["event"], "to": ["timeline"]},
    {"type": "BASED_IN", "label": "Based in", "from": ["organization"], "to": ["location"]},
    {"type": "SPOKEN_BY", "label": "Is spoken by", "from": ["race"], "to": ["language"]},
    {"type": "SPOKEN_IN", "label": "Spoken in", "from": ["language"], "to": ["location"]},
    {"type": "WRITTEN_IN", "label": "Written in", "from": ["language"], "to": ["script"]},
]


class NodeTypeSerializer(serializers.Serializer):
    type = serializers.CharField()
    label = serializers.CharField()
    pluralLabel = serializers.CharField()


class RelationTypeSerializer(serializers.Serializer):
    type = serializers.CharField()
    label = serializers.CharField()
    from_ = serializers.ListField(child=serializers.CharField(), source='from')
    to = serializers.ListField(child=serializers.CharField())

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['from'] = data.pop('from_')
        return data


@extend_schema(
    summary="List node types",
    description="Returns all possible node types with their labels",
    responses={200: NodeTypeSerializer(many=True)},
)
@api_view(['GET'])
@permission_classes([AllowAny])
def node_types(request):
    serializer = NodeTypeSerializer(NODE_TYPES, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    summary="List relation types",
    description="Returns all possible relation types, their labels",
    responses={200: RelationTypeSerializer(many=True)},
)
@api_view(['GET'])
@permission_classes([AllowAny])
def relation_types(request):
    serializer = RelationTypeSerializer(RELATION_TYPES, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
