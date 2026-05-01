from django.urls import include, path

from .views import PageDetailView, PageLikeView

app_name = 'pages'


urlpatterns = [
    path('<slug:slug>/', PageDetailView.as_view(), name='page-detail'),
    path('<slug:slug>/like/', PageLikeView.as_view(), name='page-like'),
    path('<slug:slug>/', include('apps.comments.urls')),
]
