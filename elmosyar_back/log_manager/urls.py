from django.urls import path
from . import views

app_name = 'log_manager'

urlpatterns = [
    # مدیریت لاگ‌ها (فقط سوپر یوزرها)
    path('files/', views.list_log_files, name='list_log_files'),
    path('read/', views.read_logs, name='read_logs'),
    path('download/<str:file_name>/', views.download_log_file, name='download_log_file'),
    path('clear/<str:file_name>/', views.clear_log_file, name='clear_log_file'),
    path('statistics/', views.get_log_statistics, name='get_log_statistics'),
    
    # لاگ‌های کاربران معمولی
    path('my-activity/', views.get_my_activity_logs, name='my_activity_logs'),
]