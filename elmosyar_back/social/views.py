from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import F
from django.core.paginator import Paginator

from accounts.serializers import UserSerializer
from .models import UserFollow
from notifications.models import Notification

import settings

# جایگزین کردن لاگر قدیمی
from log_manager.log_config import log_info, log_error, log_warning, log_audit

# ════════════════════════════════════════════════════════════
# 🤝 Social Endpoints
# ════════════════════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def follow_user(request, username):
    """Follow a user"""
    try:
        with transaction.atomic():
            user_to_follow = get_object_or_404(settings.AUTH_USER_MODEL, username=username)
            
            if user_to_follow == request.user:
                log_warning(f"User attempted to follow themselves", request)
                return Response({
                    'success': False,
                    'message': 'You cannot follow yourself'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if request.user.following.filter(id=user_to_follow.id).exists():
                log_warning(f"User attempted to follow already followed user", request, {'target_user': username})
                return Response({
                    'success': False,
                    'message': f'You are already following {username}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create follow relationship
            UserFollow.objects.create(follower=request.user, following=user_to_follow)
            
            # Update counts using F() to prevent race condition
            settings.AUTH_USER_MODEL.objects.filter(id=request.user.id).update(
                following_count=F('following_count') + 1
            )
            settings.AUTH_USER_MODEL.objects.filter(id=user_to_follow.id).update(
                followers_count=F('followers_count') + 1
            )
            
            # Create notification
            Notification.objects.create(
                recipient=user_to_follow,
                sender=request.user,
                notif_type='follow',
                message=f'{request.user.username} started following you'
            )
            
            # Refresh user to get updated counts
            user_to_follow.refresh_from_db()
            
            log_audit(f"User followed {username}", request, {
                'target_user_id': user_to_follow.id,
                'new_followers_count': user_to_follow.followers_count
            })
            
            return Response({
                'success': True,
                'message': f'You are now following {username}',
                'followers_count': user_to_follow.followers_count
            }, status=status.HTTP_200_OK)
            
    except Exception as e:
        log_error(f"Follow operation failed: {str(e)}", request, {'target_user': username})
        return Response({
            'success': False,
            'message': 'Follow operation failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unfollow_user(request, username):
    """Unfollow a user"""
    try:
        with transaction.atomic():
            user_to_unfollow = get_object_or_404(settings.AUTH_USER_MODEL, username=username)
            
            follow_relation = UserFollow.objects.filter(
                follower=request.user, 
                following=user_to_unfollow
            ).first()
            
            if not follow_relation:
                log_warning(f"User attempted to unfollow non-followed user", request, {'target_user': username})
                return Response({
                    'success': False,
                    'message': f'You are not following {username}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            follow_relation.delete()
            
            # Update counts using F() to prevent race condition
            settings.AUTH_USER_MODEL.objects.filter(id=request.user.id).update(
                following_count=F('following_count') - 1
            )
            settings.AUTH_USER_MODEL.objects.filter(id=user_to_unfollow.id).update(
                followers_count=F('followers_count') - 1
            )
            
            # Refresh user to get updated counts
            user_to_unfollow.refresh_from_db()
            
            log_audit(f"User unfollowed {username}", request, {
                'target_user_id': user_to_unfollow.id,
                'new_followers_count': user_to_unfollow.followers_count
            })
            
            return Response({
                'success': True,
                'message': f'You have unfollowed {username}',
                'followers_count': user_to_unfollow.followers_count
            }, status=status.HTTP_200_OK)
            
    except Exception as e:
        log_error(f"Unfollow operation failed: {str(e)}", request, {'target_user': username})
        return Response({
            'success': False,
            'message': 'Unfollow operation failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def user_followers(request, username):
    """Get user's followers with pagination"""
    user = get_object_or_404(settings.AUTH_USER_MODEL, username=username)
    
    page = int(request.GET.get('page', 1))
    per_page = min(int(request.GET.get('per_page', 50)), 100)
    
    followers = user.followers.select_related('follower')
    paginator = Paginator(followers, per_page)
    
    try:
        followers_page = paginator.page(page)
    except:
        followers_page = paginator.page(1)
    
    log_info(f"Followers list viewed for {username} page {page}", request, {
        'target_user': username,
        'total_followers': paginator.count,
        'page': page
    })
    
    # Extract user objects from follow relationships
    follower_users = [follow.follower for follow in followers_page]
    serializer = UserSerializer(follower_users, many=True, context={'request': request})
    
    return Response({
        'success': True,
        'followers': serializer.data,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count,
            'has_next': followers_page.has_next(),
            'has_previous': followers_page.has_previous(),
        }
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def user_following(request, username):
    """Get users that this user is following with pagination"""
    user = get_object_or_404(settings.AUTH_USER_MODEL, username=username)
    
    page = int(request.GET.get('page', 1))
    per_page = min(int(request.GET.get('per_page', 50)), 100)
    
    following = user.following.select_related('following')
    paginator = Paginator(following, per_page)
    
    try:
        following_page = paginator.page(page)
    except:
        following_page = paginator.page(1)
    
    log_info(f"Following list viewed for {username} page {page}", request, {
        'target_user': username,
        'total_following': paginator.count,
        'page': page
    })
    
    # Extract user objects from follow relationships
    following_users = [follow.following for follow in following_page]
    serializer = UserSerializer(following_users, many=True, context={'request': request})
    
    return Response({
        'success': True,
        'following': serializer.data,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count,
            'has_next': following_page.has_next(),
            'has_previous': following_page.has_previous(),
        }
    }, status=status.HTTP_200_OK)