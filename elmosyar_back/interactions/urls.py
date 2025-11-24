from django.urls import path
from . import views

app_name = 'interactions'

urlpatterns = [
    # Post reactions
    path('posts/<int:post_id>/like/', views.post_like, name='post_like'),
    path('posts/<int:post_id>/dislike/', views.post_dislike, name='post_dislike'),
    path('posts/<int:post_id>/comment/', views.post_comment, name='post_comment'),
    
    # Comment actions
    path('comments/<int:comment_id>/like/', views.like_comment, name='like_comment'),
    path('comments/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('comments/<int:comment_id>/update/', views.update_comment, name='update_comment'),
]