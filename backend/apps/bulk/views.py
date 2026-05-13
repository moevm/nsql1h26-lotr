"""
Views for bulk export/import endpoints.
"""

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import bulk_export, bulk_import


class BulkExportView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Bulk export of all data (admin)',
        description='Exports all lore data as a downloadable JSON file.',
        tags=['bulk'],
        responses={200: OpenApiTypes.OBJECT},
    )
    def get(self, request: Request) -> Response:
        if not getattr(request.user, 'is_admin', False):
            return Response(
                {
                    'error': {
                        'code': 'FORBIDDEN',
                        'message': 'Admin role required.',
                    }
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        return bulk_export()


class BulkImportView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Bulk import of data (admin)',
        description=(
            'Imports lore data from an uploaded JSON file, '
            'replacing current data.'
        ),
        tags=['bulk'],
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'file': {
                        'type': 'string',
                        'format': 'binary',
                    }
                },
            }
        },
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
        },
    )
    def post(self, request: Request) -> Response:
        if not getattr(request.user, 'is_admin', False):
            return Response(
                {
                    'error': {
                        'code': 'FORBIDDEN',
                        'message': 'Admin role required.',
                    }
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        file = request.FILES.get('file')
        result = bulk_import(file)
        return Response(result, status=status.HTTP_200_OK)
