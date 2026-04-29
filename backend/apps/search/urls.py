from django.urls import path

from .views import SearchView

app_name = 'search'

urlpatterns = [
    # GET /api/v1/search/
    path('', SearchView.as_view(), name='search'),
]
