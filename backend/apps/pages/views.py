from drf_spectacular.utils import (
    OpenApiParameter,
    extend_schema,
    inline_serializer,
)
from drf_spectacular.types import OpenApiTypes

from rest_framework import status, serializers
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.permissions import IsAdminRole

from .serializers import PageUpdateSerializer
from .services import (
    delete_page,
    get_page,
    update_page,
    like_page,
    unlike_page,
)


# Inline response schema for drf-spectacular
# TODO: move to an appropriate place
_ARTICLE_RESPONSE = inline_serializer(
    name="ArticleResponse",
    fields={
        "text": serializers.CharField(allow_null=True),
        "image_url": serializers.URLField(allow_null=True),
        "created_at": serializers.DateTimeField(allow_null=True),
        "updated_at": serializers.DateTimeField(allow_null=True),
    },
    allow_null=True,
)

_CATEGORY_SUMMARY = inline_serializer(
    name="CategorySummary",
    fields={
        "slug": serializers.CharField(),
        "name": serializers.CharField(),
    },
)

_PAGE_DETAIL_RESPONSE = inline_serializer(
    name="PageDetailResponse",
    fields={
        "slug": serializers.CharField(),
        "type": serializers.ChoiceField(
            choices=["character", "race", "location", "event", "organization",
                     "timeline", "item", "language", "script"],
            help_text="Entity type - discriminator for the `attributes` shape",
        ),
        "names": serializers.ListField(child=serializers.CharField()),
        "name": serializers.CharField(
            allow_null=True,
            help_text="Convenience shortcut: names[0] or null.",
        ),
        "attributes": serializers.DictField(
            help_text=(
                "Type-specific fields.  Shape depends on `type`.  "
                "See api-design.md for the full attribute list per type."
            ),
        ),
        "article": _ARTICLE_RESPONSE,
        "relations": serializers.DictField(
            help_text=(
                "Grouped by direction: "
                "{outgoing: {REL_TYPE: [{target, properties}]}, "
                "incoming: {REL_TYPE: [{from, properties}]}}. "
                "Only non-empty rel-type keys are present."
            ),
        ),
        "categories": serializers.ListField(child=_CATEGORY_SUMMARY),
        "likes_count": serializers.IntegerField(),
        "is_liked": serializers.BooleanField(
            allow_null=True,
            help_text="null for unauthenticated requests.",
        ),
        "comments_count": serializers.IntegerField(),
    },
)

_LIKE_RESPONSE = inline_serializer(
    name="LikeResponse",
    fields={
        "likes_count": serializers.IntegerField(),
        "is_liked":    serializers.BooleanField(),
    },
)

_SLUG_PARAMETER = OpenApiParameter(
    "slug",
    OpenApiTypes.STR,
    OpenApiParameter.PATH,
    description="Public page identifier.",
)


# View


class PageDetailView(APIView):
    '''
    GET  /api/v1/pages/{slug}/ - public
    PATCH /api/v1/pages/{slug}/ - admin only
    DELETE /api/v1/pages/{slug}/ - admin only
    '''

    # Permission is resolved per-method (see get_permissions below)
    permission_classes = [AllowAny]

    def get_permissions(self) -> list:
        if self.request.method in ("PATCH", "DELETE"):
            return [IsAdminRole()]
        return [AllowAny()]

    @extend_schema(
        summary="Get page detail",
        description=(
            "Returns the full wiki page for any entity type.  "
            "The `type` field acts as discriminator for the `attributes` shape.  "
            "`isLiked` is null for unauthenticated requests."
        ),
        tags=["pages"],
        parameters=[_SLUG_PARAMETER],
        responses={
            200: _PAGE_DETAIL_RESPONSE,
            404: OpenApiTypes.OBJECT,
        },
        auth=[],
    )
    def get(self, request: Request, slug: str) -> Response:
        user_id: int | None = (
            request.user.id if request.user.is_authenticated else None
        )
        data = get_page(slug, user_id=user_id)

        return Response(data)

    @extend_schema(
        summary="Partial update of a page",
        description=(
            "Admin only.  Accepts any subset of: `names`, `attributes`, "
            "`article`, `categories`, `relations`.  "
            "For `relations`: providing a key replaces *all* edges of that "
            "type; providing an empty list deletes all edges of that type; "
            "omitting a key leaves it unchanged."
        ),
        tags=["pages"],
        parameters=[_SLUG_PARAMETER],
        request=PageUpdateSerializer,
        responses={
            200: _PAGE_DETAIL_RESPONSE,
            400: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
    )
    def patch(self, request: Request, slug: str) -> Response:
        serializer = PageUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_id: int | None = (
            request.user.id if request.user.is_authenticated else None
        )
        data = update_page(
            slug, serializer.validated_data, user_id=user_id
        )

        return Response(data)

    @extend_schema(
        summary="Delete a page",
        description=(
            "Admin only.  Deletes the page node, its article node, and all "
            "edges (DETACH DELETE).  This action is irreversible."
        ),
        tags=["pages"],
        parameters=[_SLUG_PARAMETER],
        responses={
            204: None,
            403: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
    )
    def delete(self, request: Request, slug: str) -> Response:
        delete_page(slug)

        return Response(status=status.HTTP_204_NO_CONTENT)


class PageLikeView(APIView):
    '''
    PUT /api/v1/pages/{slug}/like/ - add like (idempotent)
    DELETE /api/v1/pages/{slug}/like/ - remove like (idempotent)

    Both methods require authentication.
    No request body.
    Both return {"likesCount": N, "isLiked": bool}.
    '''

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Like a page',
        description=(
            'Idempotent. Subsequent calls on an already liked page returns '
            '200 with the same sount - not an error.'
        ),
        tags=['pages'],
        parameters=[_SLUG_PARAMETER],
        request=None,
        responses={
            200: _LIKE_RESPONSE,
            401: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
    )
    def put(self, request: Request, slug: str) -> Response:
        return Response(like_page(slug, user_id=request.user.id))

    @extend_schema(
        summary="Unlike a page",
        description=(
            "Idempotent. Calling on a page that was never liked returns"
            "200 with the current count — not an error."
        ),
        tags=["pages"],
        parameters=[_SLUG_PARAMETER],
        request=None,
        responses={
            200: _LIKE_RESPONSE,
            401: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
    )
    def delete(self, request: Request, slug: str) -> Response:
        return Response(unlike_page(slug, user_id=request.user.id))
