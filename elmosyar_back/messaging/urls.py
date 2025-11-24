from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('conversations/', views.conversations_list, name='conversations_list'),
    path('conversations/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('conversations/<int:conversation_id>/send/', views.send_message, name='send_message'),
    path('conversations/start/<str:username>/', views.start_conversation, name='start_conversation'),
    path('messages/<int:message_id>/delete/', views.delete_message, name='delete_message'),
    path('messages/<int:message_id>/update/', views.update_message, name='update_message'),
]