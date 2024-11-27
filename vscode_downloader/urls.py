from django.urls import path
from . import views

app_name = 'vscode_downloader'

urlpatterns = [
    path('', views.browse_extensions, name='extension_list'),
    path('download/', views.download_extensions, name='download'),
    path('api/extensions/<str:extension_id>/', views.api_extension_details, name='api_extension_details'),
] 