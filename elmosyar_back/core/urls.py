from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    
    # Authentication
    path('api/signup/', views.signup, name='signup'),
    path('api/login/', views.login_user, name='login'),
    path('api/logout/', views.logout_user, name='logout'),
    path('api/verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('api/password-reset/request/', views.request_password_reset, name='request_password_reset'),
    path('api/password-reset/<str:token>/', views.reset_password, name='reset_password'),
    
    # Profile
    path('api/profile/', views.get_profile, name='get_profile'),
    path('api/profile/update/', views.update_profile, name='update_profile'),
    path('api/profile/update-picture/', views.update_profile_picture, name='update_profile_picture'),
    path('api/users/<str:username>/profile/', views.get_user_profile, name='get_user_profile'),
    
    # Social (Follow system)
    path('api/users/<str:username>/follow/', views.follow_user, name='follow_user'),
    path('api/users/<str:username>/unfollow/', views.unfollow_user, name='unfollow_user'),
    path('api/users/<str:username>/followers/', views.user_followers, name='user_followers'),
    path('api/users/<str:username>/following/', views.user_following, name='user_following'),
    
    # Posts and interactions
    path('api/posts/', views.posts_list_create, name='posts_list_create'),
    path('api/posts/<int:post_id>/', views.post_detail, name='post_detail'),
    path('api/posts/<int:post_id>/like/', views.post_like, name='post_like'),
    path('api/posts/<int:post_id>/dislike/', views.post_dislike, name='post_dislike'),
    path('api/posts/<int:post_id>/comment/', views.post_comment, name='post_comment'),
    path('api/posts/<int:post_id>/repost/', views.post_repost, name='post_repost'),
    path('api/posts/<int:post_id>/thread/', views.post_thread, name='post_thread'),
    path('api/posts/<int:post_id>/save/', views.save_post, name='save_post'),
    path('api/posts/<int:post_id>/unsave/', views.unsave_post, name='unsave_post'),
    path('api/posts/category/<str:category_id>/', views.posts_by_category, name='posts_by_category'),
    path('api/posts/saved/', views.saved_posts, name='saved_posts'),
    
    # Comments
    path('api/comments/<int:comment_id>/like/', views.like_comment, name='like_comment'),
    
    # User posts
    path('api/users/<str:username>/posts/', views.user_posts, name='user_posts'),
    
    # Notifications
    path('api/notifications/', views.notifications_list, name='notifications_list'),
    path('api/notifications/mark-read/', views.notifications_mark_read, name='notifications_mark_read'),
    
    # Messaging
    path('api/conversations/', views.conversations_list, name='conversations_list'),
    path('api/conversations/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('api/conversations/<int:conversation_id>/send/', views.send_message, name='send_message'),
    path('api/conversations/start/<str:username>/', views.start_conversation, name='start_conversation'),
]