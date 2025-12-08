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
    return JsonResponse({
        'message': 'Welcome to Elmosyar API',
        'version': '1.0.2',
        'apps': ['accounts', 'social', 'posts', 'interactions', 'notifications', 'messaging', 'wallet']
    })

urlpatterns = [
    path('', api_root, name='api_root'),
    path('admin/', admin.site.urls),
    
    # App routes
    path('api/', include('accounts.urls')),
    path('api/', include('social.urls')),
    path('api/posts/', include('posts.urls')),
    path('api/', include('interactions.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/', include('messaging.urls')),
    path('api/wallet/', include('wallet.urls')),
    path('api/logs/', include('log_manager.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)