from django.urls import path
from . import views

urlpatterns = [
    path('test/', views.neo4j_test_view, name='neo4j_test')
]
