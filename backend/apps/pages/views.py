from collections.abc import Sequence

from drf_spectacular.utils import OpenApiParameter, extend_schema
from drf_spectacular.types import OpenApiTypes

from rest_framework import status
from rest_framework.permissions import BasePermission, AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.permissions import IsAdminRole

from .serializers import PageUpdateSerializer
from .services import delete_page, get_page, update_page


class PageDetailView(APIView):
    '''
    GET  /api/v1/pages/{slug}/ - public
    PATCH /api/v1/pages/{slug}/ - admin only
    DELETE /api/v1/pages/{slug}/ - admin only
    '''

    # Permission is resolved per-method (see get_permissions below)
    permission_classes = [AllowAny]

    def get_permissions(self) -> list[BasePermission]:
        if self.request.method == 'GET':
            return [AllowAny()]
        if self.request.method == 'PATCH':
            return [IsAdminRole()]
        if self.request.method == 'DELETE':
            return [IsAdminRole()]

        return super().get_permissions()  # type: ignore

    @extend_schema(
        summary="Get page detail",
        description=(
            "Returns the full wiki page for any entity type.  "
            "The `type` field acts as discriminator for the `attributes` shape.  "
            "`isLiked` is null for unauthenticated requests."
        ),
        tags=["pages"],
        parameters=[
            OpenApiParameter("slug", OpenApiTypes.STR, OpenApiParameter.PATH),
        ],
        responses={
            200: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
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
        request=PageUpdateSerializer,
        responses={
            200: OpenApiTypes.OBJECT,
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
        responses={
            204: None,
            403: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
    )
    def delete(self, request: Request, slug: str) -> Response:
        delete_page(slug)

        return Response(status=status.HTTP_204_NO_CONTENT)
