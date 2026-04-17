from typing import Any

from neo4j.exceptions import ConstraintError
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.permissions import IsAdminRole

from .filters import (
    CharacterFilter,
    RaceFilter,
    LocationFilter,
    EventFilter,
    OrganizationFilter,
    TimelineFilter,
    ItemFilter,
    LanguageFilter,
    ScriptFilter,
)

from .serializers import (
    CharacterOutputSerializer, CharacterCreateSerializer,
    RaceOutputSerializer, RaceCreateSerializer,
    LocationOutputSerializer, LocationCreateSerializer,
    EventOutputSerializer, EventCreateSerializer,
    OrganizationOutputSerializer, OrganizationCreateSerializer,
    TimelineOutputSerializer, TimelineCreateSerializer,
    ItemOutputSerializer, ItemCreateSerializer,
    LanguageOutputSerializer, LanguageCreateSerializer,
    ScriptOutputSerializer, ScriptCreateSerializer,
)

from .services import (
    PaginatedResult,
    list_catalog,
    create_entity,
    slug_exists,
    CHARACTER_CONFIG,
    RACE_CONFIG,
    LOCATION_CONFIG,
    EVENT_CONFIG,
    ORGANIZATION_CONFIG,
    TIMELINE_CONFIG,
    ITEM_CONFIG,
    LANGUAGE_CONFIG,
    SCRIPT_CONFIG,
    _DEFAULT_PAGE_SIZE,
    _MAX_PAGE_SIZE,
)


# Helper functions


def _parse_bool(value: str | None) -> bool | None:
    ''' 'true'/'1' -> True, 'false'/'0' -> False, else -> None '''
    if value is None:
        return None

    return value.strip().lower() in ('true', '1', 'yes')


def _parse_int(value: str | None, default: int) -> int:
    try:
        return int(value) if value is not None else default
    except (ValueError, TypeError):
        return default


def _get_pagination_params(request: Request) -> tuple[int, int]:
    page = max(1, _parse_int(request.query_params.get('page'), 1))
    page_size = min(
        _MAX_PAGE_SIZE,
        max(1, _parse_int(
            request.query_params.get('page_size'), _DEFAULT_PAGE_SIZE
        ))
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
class _BaseCatalogView(APIView):
    '''
    Base view for catalogs.
    GET: AllowAny
    POST: IsAdminRole
    '''

    def get_permissions(self) -> list[Any]:
        if self.request.method == 'POST':
            return [IsAdminRole()]

        return [AllowAny()]


class CharacterListView(_BaseCatalogView):

    def get(self, request: Request) -> Response:
        f = CharacterFilter(
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

            race_slug=request.query_params.get('race_slug'),
            born_in_slug=request.query_params.get('born_in_slug'),
        )

        page, page_size = _get_pagination_params(request)
        sort, order = _get_sort_params(request)

        result = list_catalog(
            config=CHARACTER_CONFIG,
            filters=f,
            page=page,
            page_size=page_size,
            sort=sort,
            order=order,
            base_url=request.build_absolute_uri(request.path),
            filter_params=_filter_params_for_pagination(request),
        )

        return _paginated_response(result, CharacterOutputSerializer)

    def post(self, request: Request) -> Response:
        serializer = CharacterCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data: dict[str, Any] = serializer.validated_data

        # Needed in case of race condition
        if slug_exists(data['slug']):
            return _conflict_response(data['slug'])

        try:
            created = create_entity(CHARACTER_CONFIG, data)
        except ConstraintError:
            return _conflict_response(data['slug'])

        return Response(
            CharacterOutputSerializer(created).data,
            status=status.HTTP_201_CREATED,
        )


class RaceListView(_BaseCatalogView):

    def get(self, request: Request) -> Response:
        f = RaceFilter(
            name=request.query_params.get('name'),
            lifespan=request.query_params.get('lifespan'),
            avg_height=request.query_params.get('avg_height'),
            hair=request.query_params.get('hair'),
            eyes=request.query_params.get('eyes'),
            skin=request.query_params.get('skin'),
            weaponry=request.query_params.get('weaponry'),
            clothing=request.query_params.get('clothing'),
            distinctions=request.query_params.get('distinctions'),
        )

        page, page_size = _get_pagination_params(request)
        sort, order = _get_sort_params(request)

        result = list_catalog(
            config=RACE_CONFIG,
            filters=f,
            page=page,
            page_size=page_size,
            sort=sort,
            order=order,
            base_url=request.build_absolute_uri(request.path),
            filter_params=_filter_params_for_pagination(request),
        )

        return _paginated_response(result, RaceOutputSerializer)

    def post(self, request: Request) -> Response:
        serializer = RaceCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data: dict[str, Any] = serializer.validated_data

        if slug_exists(data['slug']):
            return _conflict_response(data['slug'])

        try:
            created = create_entity(RACE_CONFIG, data)
        except ConstraintError:
            return _conflict_response(data['slug'])

        return Response(
            RaceOutputSerializer(created).data,
            status=status.HTTP_201_CREATED,
        )


class LocationListView(_BaseCatalogView):

    def get(self, request: Request) -> Response:
        f = LocationFilter(
            name=request.query_params.get('name'),
            entity_type=request.query_params.get('entity_type'),
            population=request.query_params.get('population'),
            creation_date=request.query_params.get('creation_date'),
            destruction_date=request.query_params.get('destruction_date'),
            notable_for=request.query_params.get('notable_for'),
            is_destroyed=_parse_bool(request.query_params.get('is_destroyed')),
        )

        page, page_size = _get_pagination_params(request)
        sort, order = _get_sort_params(request)

        result = list_catalog(
            config=LOCATION_CONFIG,
            filters=f,
            page=page,
            page_size=page_size,
            sort=sort,
            order=order,
            base_url=request.build_absolute_uri(request.path),
            filter_params=_filter_params_for_pagination(request),
        )

        return _paginated_response(result, LocationOutputSerializer)

    def post(self, request: Request) -> Response:
        serializer = LocationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data: dict[str, Any] = serializer.validated_data

        if slug_exists(data['slug']):
            return _conflict_response(data['slug'])

        try:
            created = create_entity(LOCATION_CONFIG, data)
        except ConstraintError:
            return _conflict_response(data['slug'])

        return Response(
            LocationOutputSerializer(created).data,
            status=status.HTTP_201_CREATED,
        )


class EventListView(_BaseCatalogView):
    def get(self, request: Request) -> Response:
        f = EventFilter(
            name=request.query_params.get('name'),
            entity_type=request.query_params.get('entity_type'),
            start_date=request.query_params.get('start_date'),
            end_date=request.query_params.get('end_date'),
            casualties=request.query_params.get('casualties'),
            notable_for=request.query_params.get('notable_for'),
        )

        page, page_size = _get_pagination_params(request)
        sort, order = _get_sort_params(request)

        result = list_catalog(
            config=EVENT_CONFIG,
            filters=f,
            page=page,
            page_size=page_size,
            sort=sort,
            order=order,
            base_url=request.build_absolute_uri(request.path),
            filter_params=_filter_params_for_pagination(request),
        )

        return _paginated_response(result, EventOutputSerializer)

    def post(self, request: Request) -> Response:
        serializer = EventCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data: dict[str, Any] = serializer.validated_data

        if slug_exists(data['slug']):
            return _conflict_response(data['slug'])

        try:
            created = create_entity(EVENT_CONFIG, data)
        except ConstraintError:
            return _conflict_response(data['slug'])

        return Response(
            EventOutputSerializer(created).data,
            status=status.HTTP_201_CREATED,
        )


class OrganizationListView(_BaseCatalogView):

    def get(self, request: Request) -> Response:
        f = OrganizationFilter(
            name=request.query_params.get('name'),
            entity_type=request.query_params.get('entity_type'),
            founded_date=request.query_params.get('founded_date'),
            dissolved_date=request.query_params.get('dissolved_date'),
            clothing=request.query_params.get('clothing'),
            weaponry=request.query_params.get('weaponry'),
            purpose=request.query_params.get('purpose'),
            notable_for=request.query_params.get('notable_for'),
            is_dissolved=_parse_bool(request.query_params.get('is_dissolved')),
        )

        page, page_size = _get_pagination_params(request)
        sort, order = _get_sort_params(request)

        result = list_catalog(
            config=ORGANIZATION_CONFIG,
            filters=f,
            page=page,
            page_size=page_size,
            sort=sort,
            order=order,
            base_url=request.build_absolute_uri(request.path),
            filter_params=_filter_params_for_pagination(request),
        )

        return _paginated_response(result, OrganizationOutputSerializer)

    def post(self, request: Request) -> Response:
        serializer = OrganizationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data: dict[str, Any] = serializer.validated_data

        if slug_exists(data['slug']):
            return _conflict_response(data['slug'])

        try:
            created = create_entity(ORGANIZATION_CONFIG, data)
        except ConstraintError:
            return _conflict_response(data['slug'])

        return Response(
            OrganizationOutputSerializer(created).data,
            status=status.HTTP_201_CREATED,
        )


class TimelineListView(_BaseCatalogView):

    def get(self, request: Request) -> Response:
        f = TimelineFilter(
            name=request.query_params.get('name'),
            abbreviation=request.query_params.get('abbreviation'),
            start_date=request.query_params.get('start_date'),
            end_date=request.query_params.get('end_date'),
        )

        page, page_size = _get_pagination_params(request)
        sort, order = _get_sort_params(request)

        result = list_catalog(
            config=TIMELINE_CONFIG,
            filters=f,
            page=page,
            page_size=page_size,
            sort=sort,
            order=order,
            base_url=request.build_absolute_uri(request.path),
            filter_params=_filter_params_for_pagination(request),
        )

        return _paginated_response(result, TimelineOutputSerializer)

    def post(self, request: Request) -> Response:
        serializer = TimelineCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data: dict[str, Any] = serializer.validated_data

        if slug_exists(data['slug']):
            return _conflict_response(data['slug'])

        try:
            created = create_entity(TIMELINE_CONFIG, data)
        except ConstraintError:
            return _conflict_response(data['slug'])

        return Response(
            TimelineOutputSerializer(created).data,
            status=status.HTTP_201_CREATED,
        )


class ItemListView(_BaseCatalogView):

    def get(self, request: Request) -> Response:
        f = ItemFilter(
            name=request.query_params.get('name'),
            entity_type=request.query_params.get('entity_type'),
            material=request.query_params.get('material'),
            notable_for=request.query_params.get('notable_for'),
        )

        page, page_size = _get_pagination_params(request)
        sort, order = _get_sort_params(request)

        result = list_catalog(
            config=ITEM_CONFIG,
            filters=f,
            page=page,
            page_size=page_size,
            sort=sort,
            order=order,
            base_url=request.build_absolute_uri(request.path),
            filter_params=_filter_params_for_pagination(request),
        )

        return _paginated_response(result, ItemOutputSerializer)

    def post(self, request: Request) -> Response:
        serializer = ItemCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data: dict[str, Any] = serializer.validated_data

        if slug_exists(data['slug']):
            return _conflict_response(data['slug'])

        try:
            created = create_entity(ITEM_CONFIG, data)
        except ConstraintError:
            return _conflict_response(data['slug'])

        return Response(
            ItemOutputSerializer(created).data,
            status=status.HTTP_201_CREATED,
        )


class LanguageListView(_BaseCatalogView):

    def get(self, request: Request) -> Response:
        f = LanguageFilter(
            name=request.query_params.get('name'),
            family=request.query_params.get('family'),
        )

        page, page_size = _get_pagination_params(request)
        sort, order = _get_sort_params(request)

        result = list_catalog(
            config=LANGUAGE_CONFIG,
            filters=f,
            page=page,
            page_size=page_size,
            sort=sort,
            order=order,
            base_url=request.build_absolute_uri(request.path),
            filter_params=_filter_params_for_pagination(request),
        )

        return _paginated_response(result, LanguageOutputSerializer)

    def post(self, request: Request) -> Response:
        serializer = LanguageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data: dict[str, Any] = serializer.validated_data

        if slug_exists(data['slug']):
            return _conflict_response(data['slug'])

        try:
            created = create_entity(LANGUAGE_CONFIG, data)
        except ConstraintError:
            return _conflict_response(data['slug'])

        return Response(
            LanguageOutputSerializer(created).data,
            status=status.HTTP_201_CREATED,
        )


class ScriptListView(_BaseCatalogView):

    def get(self, request: Request) -> Response:
        f = ScriptFilter(name=request.query_params.get('name'))

        page, page_size = _get_pagination_params(request)
        sort, order = _get_sort_params(request)

        result = list_catalog(
            config=SCRIPT_CONFIG,
            filters=f,
            page=page,
            page_size=page_size,
            sort=sort,
            order=order,
            base_url=request.build_absolute_uri(request.path),
            filter_params=_filter_params_for_pagination(request),
        )

        return _paginated_response(result, ScriptOutputSerializer)

    def post(self, request: Request) -> Response:
        serializer = ScriptCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data: dict[str, Any] = serializer.validated_data

        if slug_exists(data['slug']):
            return _conflict_response(data['slug'])

        try:
            created = create_entity(SCRIPT_CONFIG, data)
        except ConstraintError:
            return _conflict_response(data['slug'])

        return Response(
            ScriptOutputSerializer(created).data,
            status=status.HTTP_201_CREATED,
        )
