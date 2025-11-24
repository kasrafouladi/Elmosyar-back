from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.core.paginator import Paginator
import logging

from .models import Notification
from .serializers import NotificationSerializer

logger = logging.getLogger(__name__)

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
            Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        else:
            # Mark specific notifications as read
            Notification.objects.filter(
                recipient=request.user,
                id__in=ids
            ).update(is_read=True)
        
        return Response({
            'success': True,
            'message': 'Notifications marked as read'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Mark notifications as read failed: {str(e)}")
        return Response({
            'success': False,
            'message': 'Failed to mark notifications as read'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
