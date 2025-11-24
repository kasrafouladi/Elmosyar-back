from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('signup/', views.signup, name='signup'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('token/verify/', views.VerifyTokenView.as_view(), name='token_verify'),
    path('token/refresh/', views.RefreshTokenView.as_view(), name='token_refresh'),
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('resend-verification-email/', views.resend_verification_email, name='resend_verification'),
    path('password-reset/request/', views.request_password_reset, name='password_reset_request'),
    path('password-reset/<str:token>/', views.reset_password, name='reset_password'),
    
    # Profile
    path('profile/', views.get_profile, name='get_profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('profile/update-picture/', views.update_profile_picture, name='update_profile_picture'),
    path('profile/delete-picture/', views.delete_profile_picture, name='delete_profile_picture'),
    path('users/<str:username>/profile/', views.get_user_profile, name='get_user_profile'),
]