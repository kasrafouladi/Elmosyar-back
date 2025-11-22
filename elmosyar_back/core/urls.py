from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    
    # Authentication
    path('signup/', views.signup, name='signup'),
    path('login/', views.Login.as_view(), name='login'),
    path('logout/', views.Logout.as_view(), name='logout'),

    path('token/verify/', views.VerifyTokenView.as_view(), name='token_verify'),
    path('token/refresh/', views.RefreshTokenView.as_view(), name='token_refresh'),

    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('password-reset/request/', views.request_password_reset, name='request_password_reset'),
    path('password-reset/<str:token>/', views.reset_password, name='reset_password'),
    
    # Profile
    path('profile/', views.get_profile, name='get_profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('profile/update-picture/', views.update_profile_picture, name='update_profile_picture'),
    path('profile/delete-picture/', views.delete_profile_picture, name='delete_profile_picture'),
    path('users/<str:username>/profile/', views.get_user_profile, name='get_user_profile'),
    
    # Social (Follow system)
    path('users/<str:username>/follow/', views.follow_user, name='follow_user'),
    path('users/<str:username>/unfollow/', views.unfollow_user, name='unfollow_user'),
    path('users/<str:username>/followers/', views.user_followers, name='user_followers'),
    path('users/<str:username>/following/', views.user_following, name='user_following'),
    
    # Posts and interactions
    path('posts/', views.posts_list_create, name='posts_list_create'),
    path('posts/<int:post_id>/', views.post_detail, name='post_detail'),
    path('posts/<int:post_id>/like/', views.post_like, name='post_like'),
    path('posts/<int:post_id>/dislike/', views.post_dislike, name='post_dislike'),
    path('posts/<int:post_id>/comment/', views.post_comment, name='post_comment'),
    path('posts/<int:post_id>/repost/', views.post_repost, name='post_repost'),
    path('posts/<int:post_id>/thread/', views.post_thread, name='post_thread'),
    path('posts/<int:post_id>/save/', views.save_post, name='save_post'),
    path('posts/<int:post_id>/unsave/', views.unsave_post, name='unsave_post'),
    path('posts/<int:post_id>/delete/', views.delete_post, name='delete_post'),
    path('posts/<int:post_id>/update/', views.update_post, name='update_post'),
    path('posts/category/<str:category_id>/', views.posts_by_category, name='posts_by_category'),
    path('posts/saved/', views.saved_posts, name='saved_posts'),
    
    # Comments
    path('comments/<int:comment_id>/like/', views.like_comment, name='like_comment'),
    path('comments/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('comments/<int:comment_id>/update/', views.update_comment, name='update_comment'),
    
    # User posts
    path('users/<str:username>/posts/', views.user_posts, name='user_posts'),
    
    # Notifications
    path('notifications/', views.notifications_list, name='notifications_list'),
    path('notifications/mark-read/', views.notifications_mark_read, name='notifications_mark_read'),
    
    # Messaging
    path('conversations/', views.conversations_list, name='conversations_list'),
    path('conversations/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('conversations/<int:conversation_id>/send/', views.send_message, name='send_message'),
    path('conversations/start/<str:username>/', views.start_conversation, name='start_conversation'),
    path('messages/<int:message_id>/delete/', views.delete_message, name='delete_message'),
    path('messages/<int:message_id>/update/', views.update_message, name='update_message'),
]