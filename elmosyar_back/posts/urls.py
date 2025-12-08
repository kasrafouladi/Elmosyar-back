from django.urls import path
from . import views

app_name = 'posts'

urlpatterns = [
    path('', views.posts_list_create, name='posts_list_create'),
    path('<int:post_id>/', views.post_detail, name='post_detail'),
    path('<int:post_id>/repost/', views.post_repost, name='post_repost'),
    path('<int:post_id>/thread/', views.post_thread, name='post_thread'),
    path('<int:post_id>/save/', views.save_post, name='save_post'),
    path('<int:post_id>/unsave/', views.unsave_post, name='unsave_post'),
    path('<int:post_id>/delete/', views.delete_post, name='delete_post'),
    path('<int:post_id>/update/', views.update_post, name='update_post'),
    path('category/<str:category_id>/', views.posts_by_category, name='posts_by_category'),
    path('saved/', views.saved_posts, name='saved_posts'),
    path('users/<str:username>/', views.user_posts, name='user_posts'),

    path('formats/upload/', views.upload_category_format, name='upload_category_format'),
    path('formats/<str:cat>/', views.get_format, name='get_format'),
    path('formats/<str:cat>/delete/', views.delete_category_format, name='delete_category_format'),
]