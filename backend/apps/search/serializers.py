'''
Serializers for the search app.

SearchQuerySerializer validates query parameters from GET /api/v1/search/.
Used by the view to validate request.query_params before calling the service.

SearchResultSerializer is used only in @extend_schema for Swagger UI.
The service already returns plain dicts; no runtime serialization needed.
'''

from rest_framework import serializers

from .queries import VALID_TYPES


class SearchQuerySerializer(serializers.Serializer):
    '''
    Validates GET /api/v1/search query parameters
    '''

    q = serializers.CharField(
        min_length=2,
        max_length=200,
        trim_whitespace=True,
        help_text='Searcg query (min 2 chars).'
    )
    types = serializers.CharField(
        required=False,
        allow_blank=True,
        default='',
        help_text=(
            f'Comma-separated entity types to restrict the search to. '
            f'Valid values: {", ".join(sorted(VALID_TYPES))}. '
            f'Omit to search all types.'
        ),
    )
    limit = serializers.IntegerField(
        min_value=1,
        max_value=20,
        default=5,
        help_text='Max number of results to return (1-20, default 5).'
    )


class SearchResultSerializer(serializers.Serializer):
    '''
    Output shape of one search result.
    Used only for Swagger schema generation.
    '''

    slug = serializers.CharField()
    type = serializers.ChoiceField(
        choices=sorted(VALID_TYPES),
        help_text='Entity type.'
    )
    name = serializers.CharField(
        allow_null=True,
        help_text='Primary name (names[0]) of the entity.'
    )
    names = serializers.ListField(
        child=serializers.CharField(),
        allow_null=True,
        help_text='All names or the entity.')
    image_url = serializers.URLField(
        allow_null=True,
        help_text='URL of the entity\'s article image, if any.'
    )
