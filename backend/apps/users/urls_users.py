'''
URL patterns for /api/v1/users/ endpoints.

Kept separate from urls.py (which handles /api/v1/auth/*) so each URL module
has a single responsibility and config/urls.py can include them independently.
'''
from django.urls import path

from apps.users import views

app_name = 'users'

urlpatterns = [
    path('', views.UserListView.as_view(), name='user-list'),
    path('<str:username>/', views.UserDetailView.as_view(), name='user-detail'),
    path('<str:username>/liked/', views.UserLikedPagesView.as_view(), name='user-liked'),
]