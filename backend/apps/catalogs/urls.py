from django.urls import path

from .views import (
    CharacterListView,
    EventListView,
    ItemListView,
    LanguageListView,
    LocationListView,
    OrganizationListView,
    RaceListView,
    ScriptListView,
    TimelineListView,
)

app_name = 'catalogs'

urlpatterns = [
    path('characters/', CharacterListView.as_view(), name='character-list'),
    path('races/', RaceListView.as_view(), name='race-list'),
    path('locations/', LocationListView.as_view(), name='locations-list'),
    path('events/', EventListView.as_view(), name='event-list'),
    path(
        'organizations/',
        OrganizationListView.as_view(),
        name='organization-list'
    ),
    path('timelines/', TimelineListView.as_view(), name='timeline-list'),
    path('items/', ItemListView.as_view(), name='item-list'),
    path('languages/', LanguageListView.as_view(), name='language-list'),
    path('scripts/', ScriptListView.as_view(), name='script-list'),
]