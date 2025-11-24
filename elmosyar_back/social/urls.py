from django.urls import path
from . import views

app_name = 'social'

urlpatterns = [
    path('users/<str:username>/follow/', views.follow_user, name='follow_user'),
    path('users/<str:username>/unfollow/', views.unfollow_user, name='unfollow_user'),
    path('users/<str:username>/followers/', views.user_followers, name='user_followers'),
    path('users/<str:username>/following/', views.user_following, name='user_following'),
]