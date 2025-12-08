from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.core.paginator import Paginator

from .models import Notification
from .serializers import NotificationSerializer

# جایگزین کردن لاگر قدیمی
from log_manager.log_config import log_info, log_error, log_warning

# ════════════════════════════════════════════════════════════
# 🔔 Notification Endpoints
# ════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notifications_list(request):
    """Get user notifications with pagination"""
    page = int(request.GET.get('page', 1))
    per_page = min(int(request.GET.get('per_page', 20)), 100)
    
    notifications = Notification.objects.filter(
        recipient=request.user
    ).select_related('sender', 'post', 'comment').order_by('-created_at')
    
    paginator = Paginator(notifications, per_page)
    try:
        notifications_page = paginator.page(page)
    except:
        notifications_page = paginator.page(1)
    
    serializer = NotificationSerializer(notifications_page, many=True, context={'request': request})
    
    # لاگ کردن دسترسی
    log_info(f"User viewed notifications page {page}", request)
    
    return Response({
        'success': True,
        'notifications': serializer.data,
        'unread_count': Notification.objects.filter(recipient=request.user, is_read=False).count(),
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count,
            'has_next': notifications_page.has_next(),
            'has_previous': notifications_page.has_previous(),
        }
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def notifications_mark_read(request):
    """Mark notifications as read"""
    ids = request.data.get('ids', [])
    
    try:
        if not ids:
            # Mark all as read
            updated_count = Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
            log_info(f"User marked all notifications as read ({updated_count} notifications)", request)
        else:
            # Mark specific notifications as read
            updated_count = Notification.objects.filter(
                recipient=request.user,
                id__in=ids
            ).update(is_read=True)
            log_info(f"User marked {updated_count} specific notifications as read", request, {'ids': ids})
        
        return Response({
            'success': True,
            'message': 'Notifications marked as read'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        log_error(f"Mark notifications as read failed: {str(e)}", request, {'ids': ids})
        return Response({
            'success': False,
            'message': 'Failed to mark notifications as read'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)