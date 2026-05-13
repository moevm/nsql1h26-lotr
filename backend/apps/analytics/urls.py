from django.urls import path

from .views import CustomAnalyticsView, GlobalStatsView, NeighborsView, ShortestPathView

urlpatterns = [
    path('global/', GlobalStatsView.as_view(), name='analytics-global'),
    path('neighbors/', NeighborsView.as_view(), name='analytics-neighbors'),
    path("shortest-path/", ShortestPathView.as_view(), name="analytics-shortest-path"),
    path("custom/", CustomAnalyticsView.as_view(), name="analytics-custom"),
]
