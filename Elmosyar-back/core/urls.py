from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/signup/', views.signup, name='signup'),
    path('api/login/', views.login_user, name='login'),
    path('api/logout/', views.logout_user, name='logout'),
    path('api/verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('api/profile/', views.get_profile, name='get_profile'),
    path('api/profile/update/', views.update_profile, name='update_profile'),
    path('api/profile/update-picture/', views.update_profile_picture, name='update_profile_picture'),
    path('api/password-reset/request/', views.request_password_reset, name='request_password_reset'),
    path('api/password-reset/<str:token>/', views.reset_password, name='reset_password'),
    
    # Posts and interactions
    path('api/posts/', views.posts_list_create, name='posts_list_create'),
    path('api/posts/<int:post_id>/', views.post_detail, name='post_detail'),
    path('api/posts/<int:post_id>/like/', views.post_like, name='post_like'),
    path('api/posts/<int:post_id>/dislike/', views.post_dislike, name='post_dislike'),
    path('api/posts/<int:post_id>/comment/', views.post_comment, name='post_comment'),
    path('api/posts/<int:post_id>/repost/', views.post_repost, name='post_repost'),
    path('api/posts/<int:post_id>/thread/', views.post_thread, name='post_thread'),
    path('api/posts/category/<str:category_id>/', views.posts_by_category, name='posts_by_category'),
    path('api/users/<str:username>/posts/', views.user_posts, name='user_posts'),
    
    # Notifications
    path('api/notifications/', views.notifications_list, name='notifications_list'),
    path('api/notifications/mark-read/', views.notifications_mark_read, name='notifications_mark_read'),
    
    # Pages
    path('posts/', views.posts_list_page, name='posts_list_page'),
    path('posts/create/', views.create_post_page, name='create_post_page'),
    path('posts/<int:post_id>/', views.post_detail_page, name='post_detail_page'),
    path('profiles/<str:username>/', views.profile_page, name='profile_page'),
    path('profiles/<str:username>/posts/', views.user_posts_page, name='user_posts_page'),
    path('explore/', views.explore_room_page, name='explore_room_page'),
    path('reset-password/', views.reset_password_page, name='reset_password_page'),
]