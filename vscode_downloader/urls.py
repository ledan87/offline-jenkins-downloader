from django.urls import path
from . import views

app_name = 'vscode_downloader'

urlpatterns = [
    path('', views.browse_extensions, name='extension_list'),
    path('api/download/', views.api_download_extensions, name='api_download_extensions'),
    path('api/bulk-download/start/', views.api_start_bulk_download, name='api_start_bulk_download'),
    path('api/bulk-download/status/<str:download_id>/', views.api_download_status, name='api_bulk_download_status'),
    path('api/bulk-download/zip/<str:download_id>/', views.api_get_bulk_download_zip, name='api_get_bulk_download_zip'),
    path('api/extensions/<str:extension_id>/', views.api_extension_details, name='api_extension_details'),
    path('api/extensions/<str:extension_id>/compatible/<str:vscode_target_version>/', 
         views.api_get_compatible_version, name='api_get_compatible_version'),
    path('api/extensions/<str:extension_id>/download/', views.api_start_extension_download, name='api_start_extension_download'),
    path('api/download/status/<str:download_id>/', views.api_download_status, name='api_download_status'),
] 