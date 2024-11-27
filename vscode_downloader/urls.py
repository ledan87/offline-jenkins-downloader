from django.urls import path
from . import views

app_name = 'vscode_downloader'

urlpatterns = [
    path('', views.browse_extensions, name='extension_list'),
    path('api/download/', views.api_download_extensions, name='api_download_extensions'),
    path('api/extensions/<str:extension_id>/', views.api_extension_details, name='api_extension_details'),
] 