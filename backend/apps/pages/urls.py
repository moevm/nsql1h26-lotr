from django.urls import path

from .views import PageDetailView

app_name = 'pages'


urlpatterns = [
    path('pages/<slug:slug>/', PageDetailView.as_view(), name='page-detail'),
]
