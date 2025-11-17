from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('api/signup/', views.signup, name='signup'),
    path('api/login/', views.login_user, name='login'),
    path('api/logout/', views.logout_user, name='logout'),
    path('api/verify-email/<str:token>/', views.verify_email, name='verify_email'),
    
    # Profile
    path('api/profile/', views.get_profile, name='get_profile'),
    path('api/profile/update/', views.update_profile, name='update_profile'),
    path('api/profile/update-picture/', views.update_profile_picture, name='update_profile_picture'),
    
    # Password Reset
    path('api/password-reset/request/', views.request_password_reset, name='request_password_reset'),
    path('api/password-reset/<str:token>/', views.reset_password, name='reset_password'),
    
    # Posts
    path('api/posts/', views.posts_list_create, name='posts_list_create'),
    path('api/posts/<int:post_id>/', views.post_detail, name='post_detail'),
    path('api/posts/<int:post_id>/thread/', views.post_thread, name='post_thread'),
    path('api/posts/<int:post_id>/comments/', views.post_comments, name='post_comments'),
    path('api/posts/category/<str:category_id>/', views.posts_by_category, name='posts_by_category'),
    path('api/users/<str:username>/posts/', views.user_posts, name='user_posts'),
    
    # Post Interactions
    path('api/posts/<int:post_id>/like/', views.post_like, name='post_like'),
    path('api/posts/<int:post_id>/dislike/', views.post_dislike, name='post_dislike'),
    path('api/posts/<int:post_id>/comment/', views.post_comment, name='post_comment'),
    path('api/posts/<int:post_id>/repost/', views.post_repost, name='post_repost'),
    
    # Notifications
    path('api/notifications/', views.notifications_list, name='notifications_list'),
    path('api/notifications/mark-read/', views.notifications_mark_read, name='notifications_mark_read'),
]