"""
URL configuration for elmosyar_back project.

Pure REST API - No HTML rendering
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

def api_root(request):
    """API root endpoint"""
    return JsonResponse({
        'message': 'Welcome to Elmosyar API',
        'version': '1.0.0',
        'endpoints': {
            'auth': {
                'signup': '/api/signup/',
                'login': '/api/login/',
                'logout': '/api/logout/',
                'verify_email': '/api/verify-email/<token>/',
                'password_reset_request': '/api/password-reset/request/',
                'password_reset': '/api/password-reset/<token>/',
            },
            'profile': {
                'get_profile': '/api/profile/',
                'update_profile': '/api/profile/update/',
                'update_picture': '/api/profile/update-picture/',
                'get_user': '/api/users/<username>/profile/',
                'user_posts': '/api/users/<username>/posts/',
            },
            'social': {
                'follow': '/api/users/<username>/follow/',
                'unfollow': '/api/users/<username>/unfollow/',
                'followers': '/api/users/<username>/followers/',
                'following': '/api/users/<username>/following/',
            },
            'posts': {
                'list_create': '/api/posts/',
                'detail': '/api/posts/<id>/',
                'like': '/api/posts/<id>/like/',
                'dislike': '/api/posts/<id>/dislike/',
                'comment': '/api/posts/<id>/comment/',
                'repost': '/api/posts/<id>/repost/',
                'thread': '/api/posts/<id>/thread/',
                'by_category': '/api/posts/category/<category>/',
                'saved_posts': '/api/posts/saved/',
                'save_post': '/api/posts/<id>/save/',
                'unsave_post': '/api/posts/<id>/unsave/',
            },
            'comments': {
                'like': '/api/comments/<id>/like/',
            },
            'notifications': {
                'list': '/api/notifications/',
                'mark_read': '/api/notifications/mark-read/',
            },
            'messaging': {
                'conversations': '/api/conversations/',
                'conversation_detail': '/api/conversations/<id>/',
                'send_message': '/api/conversations/<id>/send/',
                'start_conversation': '/api/conversations/start/<username>/',
            }
        }
    })

urlpatterns = [
    # API root
    path('', api_root, name='api_root'),
    
    # API routes - تغییر داده شده
    path('api/', include('core.urls')),
    
    # Admin panel
    path('admin/', admin.site.urls),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)