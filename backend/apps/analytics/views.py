
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializer import GlobalStatsSerializer
from .services import global_stats


class GlobalStatsView(APIView):
    '''
    GET /api/v1/analytics/global

    Returns aggregated statistics for the entire LotR wiki graph.
    Public.
    Results are cached for 5 minutes server-side.
    '''

    permission_classes = [AllowAny]
    @extend_schema(
        summary='Global wiki statistics',
        description=(
            'Returns aggregated statistics for the entire LotR wiki graph: '
            'entity counts, character breakdowns, engagement metrics, and '
            'most-connected nodes.  Results are cached server-side for 5 minutes.'
        ),
        tags=['analytics'],
        responses={200: GlobalStatsSerializer},
        auth=[],
    )
    def get(self, request: Request) -> Response:  # noqa: ARG002
        return Response(global_stats())
