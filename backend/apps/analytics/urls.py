from django.urls import path

from .views import GlobalStatsView

urlpatterns = [
    path('global/', GlobalStatsView.as_view(), name='analytics-global'),
]
