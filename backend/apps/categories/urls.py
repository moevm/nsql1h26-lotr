from django.urls import path

from .views import (
    CategoryDetailView,
    CategoryListCreateView,
    CategoryTreeView,
)

app_name = 'categories'

urlpatterns = [
    path(
        'categories/',
        CategoryListCreateView.as_view(),
        name='category-list-create',
    ),
    path(
        'categories/tree/',
        CategoryTreeView.as_view(),
        name='category-tree',
    ),
    path(
        'categories/<slug:slug>/',
        CategoryDetailView.as_view(),
        name='category-detail',
    ),
]
