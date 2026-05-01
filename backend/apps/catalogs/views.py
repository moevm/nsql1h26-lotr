from typing import Any

from neo4j.exceptions import ConstraintError
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.pages.enums import EntityType
from apps.pages.queries import normalize_patch_attributes
from apps.pages.serializers import PageCreateSerializer
from apps.pages.services import create_page
from apps.users.permissions import IsAdminRole

from .constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from .filters import (
    CharacterFilter,
    CypherWhereFilter,
    EventFilter,
    ItemFilter,
    LanguageFilter,
    LocationFilter,
    OrganizationFilter,
    RaceFilter,
    ScriptFilter,
    TimelineFilter,
)
from .serializers import (
    CharacterOutputSerializer,
    EventOutputSerializer,
    ItemOutputSerializer,
    LanguageOutputSerializer,
    LocationOutputSerializer,
    OrganizationOutputSerializer,
    RaceOutputSerializer,
    ScriptOutputSerializer,
    TimelineOutputSerializer,
)
from .services import (
    CHARACTER_CONFIG,
    EVENT_CONFIG,
    ITEM_CONFIG,
    LANGUAGE_CONFIG,
    LOCATION_CONFIG,
    ORGANIZATION_CONFIG,
    RACE_CONFIG,
    SCRIPT_CONFIG,
    TIMELINE_CONFIG,
    EntityConfig,
    PaginatedResult,
    list_catalog,
    slug_exists,
)

# Parsing helper functions


def _parse_bool(value: str | None) -> bool | None:
    ''' 'true'/'1' -> True, 'false'/'0' -> False, else -> None '''
    if value is None:
        return None

    normalized = value.strip().lower()

    if normalized in ('true', '1', 'yes'):
        return True
    if normalized in ('false', '0', 'no'):
        return False

    return None


def _parse_int(value: str | None, default: int) -> int:
    try:
        return int(value) if value is not None else default
    except (ValueError, TypeError):
        return default


def _get_pagination_params(request: Request) -> tuple[int, int]:
    page = max(1, _parse_int(request.query_params.get('page'), 1))
    page_size = min(
        MAX_PAGE_SIZE,
        max(1,_parse_int(request.query_params.get('page_size'), DEFAULT_PAGE_SIZE))
    )

    return page, page_size


def _get_sort_params(request: Request) -> tuple[str | None, str | None]:
    sort = request.query_params.get('sort') or None
    order = request.query_params.get('order') or None

    return sort, order


def _filter_params_for_pagination(request: Request) -> dict[str, Any]:
    '''All query params except page and page_size - for next/previous URL'''

    return {
        k: v
        for k, v in request.query_params.items()
        if k not in ('page', 'page_size')
    }


def _paginated_response(
        result: PaginatedResult,
        serializer_class: type
) -> Response:
    return Response({
        'count': result.count,
        'next': result.next,
        'previous': result.previous,
        'results': serializer_class(result.results, many=True).data
    })


def _conflict_response(slug: str) -> Response:
    return Response(
        {
            'error': {
                'code': 'CONFLICT',
                'message': f'PAGE with slug \'{slug}\' already exists.',
                'fields': {'slug': ['This slug is already taken.']},
            }
        },
        status=status.HTTP_409_CONFLICT,
    )


# Base class for similar catalog views
# Concrete views declare three class attributes and override build_filter()
# GET and POST logic is implemented once here and never repeated
class CatalogView(APIView):
    '''
    Abstract base for catalog list/create endpoints.
    GET: AllowAny
    POST: IsAdminRole

    Subclass protocol:
        config = <EntityConfig>
        output_serializer_class = <OutputSerializer>  # for GET list only

        def build_filter(self, request) -> <FilterDataclass>: ...
    '''

    config: EntityConfig
    output_serializer_class: type

    def get_permissions(self) -> list[Any]:
        if self.request.method == 'POST':
            return [IsAdminRole()]

        return [AllowAny()]

    def build_filter(self, request: Request) -> CypherWhereFilter:
        raise NotImplementedError

    # GET /{catalog}/
    def get(self, request: Request) -> Response:
        filters = self.build_filter(request)
        page, page_size = _get_pagination_params(request)
        sort, order = _get_sort_params(request)
        result = list_catalog(
            config=self.config,
            filters=filters,
            page=page,
            page_size=page_size,
            sort=sort,
            order=order,
            base_url=request.build_absolute_uri(request.path),
            filter_params=_filter_params_for_pagination(request)
        )

        return _paginated_response(result, self.output_serializer_class)

    # POST /{catalog}/
    def post(self, request: Request) -> Response:
        '''
        Create a new entity.

        Accepts the same body shape as PATCH /pages/{slug}/:
            slug (required) - the new page's public identifier
            names (required) - at least one name
            attributes (optional) - entity type-specific fields (snake_case)
            article (optional) - {text, image_url}
            categories (optional) - list of category slugs
            relations (optional) - {outgoing: {...}, incoming: {...}}

        Returns the same full-page representation as GET /pages/{slug}/.
        '''
        serializer = PageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data: dict[str, Any] = serializer.validated_data
        slug = data['slug']

        # Pre-check avoids a round-trip on the happy path;
        # ConstraintError handles the TOCTOU race in unlikely concurrent case.
        if slug_exists(slug):
            return _conflict_response(slug)

        # Translate snake_case attribute keys → Neo4j camelCase property names.
        # normalize_patch_attributes also validates enum values (e.g. gender).
        attrs = normalize_patch_attributes(
            data.get('attributes') or {}, EntityType(self.config.entity_type)
        )

        try:
            page = create_page(
                node_labels=self.config.node_labels,
                slug=slug,
                names=data['names'],
                attrs=attrs,
                article=data.get('article'),
                categories=data.get('categories'),
                relations=data.get('relations'),
                entity_type=EntityType(self.config.entity_type),
                user_id=None,
            )
        except ConstraintError:
            return _conflict_response(slug)

        return Response(page, status=status.HTTP_201_CREATED)


# Concrete catalog views


class CharacterListView(CatalogView):
    config = CHARACTER_CONFIG
    output_serializer_class = CharacterOutputSerializer

    def build_filter(self, request: Request) -> CharacterFilter:
        return CharacterFilter(
            name=request.query_params.get('name'),
            titles=request.query_params.get('titles'),
            gender=request.query_params.get('gender'),
            is_alive=_parse_bool(request.query_params.get('is_alive')),
            birth_date=request.query_params.get('birth_date'),
            death_date=request.query_params.get('death_date'),
            hair=request.query_params.get('hair'),
            eyes=request.query_params.get('eyes'),
            height=request.query_params.get('height'),
            weapon=request.query_params.get('weapon'),
            clothing=request.query_params.get('clothing'),
            notable_for=request.query_params.get('notable_for'),

            race=request.query_params.get('race'),
            organization=request.query_params.get('organization'),
            event=request.query_params.get('event'),
            item=request.query_params.get('item'),
            location=request.query_params.get('location'),
        )


class RaceListView(CatalogView):
    config = RACE_CONFIG
    output_serializer_class = RaceOutputSerializer

    def build_filter(self, request: Request) -> RaceFilter:
        return RaceFilter(
            name=request.query_params.get('name'),
            lifespan=request.query_params.get('lifespan'),
            avg_height=request.query_params.get('avg_height'),
            hair=request.query_params.get('hair'),
            eyes=request.query_params.get('eyes'),
            skin=request.query_params.get('skin'),
            weaponry=request.query_params.get('weaponry'),
            clothing=request.query_params.get('clothing'),
            distinctions=request.query_params.get('distinctions'),

            location=request.query_params.get('location'),
        )


class LocationListView(CatalogView):
    config = LOCATION_CONFIG
    output_serializer_class = LocationOutputSerializer

    def build_filter(self, request: Request) -> LocationFilter:
        return LocationFilter(
            name=request.query_params.get('name'),
            entity_type=request.query_params.get('entity_type'),
            population=request.query_params.get('population'),
            creation_date=request.query_params.get('creation_date'),
            destruction_date=request.query_params.get('destruction_date'),
            notable_for=request.query_params.get('notable_for'),
            is_destroyed=_parse_bool(request.query_params.get('is_destroyed')),

            character=request.query_params.get('character'),
            event=request.query_params.get('event'),
            organization=request.query_params.get('organization'),
        )


class EventListView(CatalogView):
    config = EVENT_CONFIG
    output_serializer_class = EventOutputSerializer

    def build_filter(self, request: Request) -> EventFilter:
        return EventFilter(
            name=request.query_params.get('name'),
            entity_type=request.query_params.get('entity_type'),
            start_date=request.query_params.get('start_date'),
            end_date=request.query_params.get('end_date'),
            casualties=request.query_params.get('casualties'),
            notable_for=request.query_params.get('notable_for'),

            character=request.query_params.get('character'),
            location=request.query_params.get('location'),
        )


class OrganizationListView(CatalogView):
    config = ORGANIZATION_CONFIG
    output_serializer_class = OrganizationOutputSerializer

    def build_filter(self, request: Request) -> OrganizationFilter:
        return OrganizationFilter(
            name=request.query_params.get('name'),
            entity_type=request.query_params.get('entity_type'),
            founded_date=request.query_params.get('founded_date'),
            dissolved_date=request.query_params.get('dissolved_date'),
            clothing=request.query_params.get('clothing'),
            weaponry=request.query_params.get('weaponry'),
            purpose=request.query_params.get('purpose'),
            notable_for=request.query_params.get('notable_for'),
            is_dissolved=_parse_bool(request.query_params.get('is_dissolved')),

            character=request.query_params.get('character'),
            location=request.query_params.get('location'),
        )


class TimelineListView(CatalogView):
    config = TIMELINE_CONFIG
    output_serializer_class = TimelineOutputSerializer

    def build_filter(self, request: Request) -> TimelineFilter:
        return TimelineFilter(
            name=request.query_params.get('name'),
            abbreviation=request.query_params.get('abbreviation'),
            start_date=request.query_params.get('start_date'),
            end_date=request.query_params.get('end_date'),
        )


class ItemListView(CatalogView):
    config = ITEM_CONFIG
    output_serializer_class = ItemOutputSerializer

    def build_filter(self, request: Request) -> ItemFilter:
        return ItemFilter(
            name=request.query_params.get('name'),
            entity_type=request.query_params.get('entity_type'),
            material=request.query_params.get('material'),
            notable_for=request.query_params.get('notable_for'),

            character=request.query_params.get('character'),
        )


class LanguageListView(CatalogView):
    config = LANGUAGE_CONFIG
    output_serializer_class = LanguageOutputSerializer

    def build_filter(self, request: Request) -> LanguageFilter:
        return LanguageFilter(
            name=request.query_params.get('name'),
            family=request.query_params.get('family'),
        )


class ScriptListView(CatalogView):
    config = SCRIPT_CONFIG
    output_serializer_class = ScriptOutputSerializer

    def build_filter(self, request: Request) -> ScriptFilter:
        return ScriptFilter(name=request.query_params.get('name'))
