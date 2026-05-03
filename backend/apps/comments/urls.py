from django.urls import path

from .views import CommentDetailView, CommentListCreateView

app_name = 'comments'

urlpatterns = [
    path('comments/', CommentListCreateView.as_view(), name='comment-list-create'),
    path(
        'comments/<str:comment_id>/', CommentDetailView.as_view(), name='comment-detail'
    ),
]
