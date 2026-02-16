from django.urls import path
from . import views

urlpatterns = [
    path('', views.neo4j_test_view, name='index')
]
