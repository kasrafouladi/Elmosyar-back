from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notifications_list, name='notifications_list'),
    path('mark-read/', views.notifications_mark_read, name='notifications_mark_read'),
]