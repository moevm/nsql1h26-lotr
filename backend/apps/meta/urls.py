from django.urls import path

from . import views

urlpatterns = [
    path('node-types/', views.node_types, name='node-types'),
    path('relation-types/', views.relation_types, name='relation-types'),
]
