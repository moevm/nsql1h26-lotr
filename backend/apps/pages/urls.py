from django.urls import path

from .views import PageDetailView, PageLikeView

app_name = 'pages'


urlpatterns = [
    path('pages/<slug:slug>/', PageDetailView.as_view(), name='page-detail'),
    path('pages/<slug:slug>/like/', PageLikeView.as_view(), name='page-like')
]
