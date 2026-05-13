from django.urls import path

from .views import BulkExportView, BulkImportView

app_name = 'bulk'

urlpatterns = [
    path('export/', BulkExportView.as_view(), name='bulk-export'),
    path('import/', BulkImportView.as_view(), name='bulk-import'),
]
