from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import transaction

from posts.models import Post
from .models import Reaction, Comment
from .serializers import CommentSerializer
from notifications.models import Notification

import settings

# جایگزین کردن لاگر قدیمی
from log_manager.log_config import log_info, log_error, log_warning, log_audit

MAX_COMMENT_CONTENT_LENGTH = 1000


def _handle_post_reaction(request, post_id, reaction_type):
    """Helper function to handle post reactions"""
    try:
        with transaction.atomic():
            post = get_object_or_404(Post, id=post_id)
            
            if post.author == request.user:
                log_warning(f"User tried to {reaction_type} their own post", request, {
                    'post_id': post_id,
                    'reaction_type': reaction_type
                })
                return {
                    'success': False,
                    'message': f'You cannot {reaction_type} your own post'
                }, status.HTTP_400_BAD_REQUEST
            
            existing_reaction = Reaction.objects.filter(user=request.user, post=post).first()
            
            if existing_reaction and existing_reaction.reaction == reaction_type:
                # Remove reaction
                existing_reaction.delete()
                action = f'un{reaction_type}d'
                user_reaction = None
                log_info(f"User removed {reaction_type} from post {post_id}", request)
            else:
                # Add/change reaction
                if existing_reaction:
                    existing_reaction.delete()
                
                Reaction.objects.create(user=request.user, post=post, reaction=reaction_type)
                
                # Create notification for like (not for dislike)
                if reaction_type == 'like' and post.author != request.user:
                    Notification.objects.create(
                        recipient=post.author,
                        sender=request.user,
                        notif_type='like',
                        post=post,
                        message=f'{request.user.username} liked your post'
                    )
                
                action = f'{reaction_type}d'
                user_reaction = reaction_type
                log_info(f"User {reaction_type}d post {post_id}", request, {
                    'post_author': post.author.username
                })
            
            # Get updated counts
            likes_count = post.reactions.filter(reaction='like').count()
            dislikes_count = post.reactions.filter(reaction='dislike').count()
            
            return {
                'success': True,
                'message': action.capitalize(),
                'likes_count': likes_count,
                'dislikes_count': dislikes_count,
                'user_reaction': user_reaction
            }, status.HTTP_200_OK
            
    except Exception as e:
        log_error(f"Reaction handling failed: {str(e)}", request, {
            'post_id': post_id,
            'reaction_type': reaction_type
        })
        return {
            'success': False,
            'message': 'Reaction operation failed'
        }, status.HTTP_500_INTERNAL_SERVER_ERROR


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def post_like(request, post_id):
    """Like/unlike a post"""
    result, status_code = _handle_post_reaction(request, post_id, 'like')
    return Response(result, status=status_code)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def post_dislike(request, post_id):
    """Dislike/remove dislike from a post"""
    result, status_code = _handle_post_reaction(request, post_id, 'dislike')
    return Response(result, status=status_code)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def post_comment(request, post_id):
    """Add comment to a post"""
    try:
        with transaction.atomic():
            post = get_object_or_404(Post, id=post_id)
            
            content = request.data.get('content', '').strip()
            parent_id = request.data.get('parent')
            
            if not content:
                log_warning("Attempt to post empty comment", request, {'post_id': post_id})
                return Response({
                    'success': False,
                    'message': 'Comment content required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if len(content) > MAX_COMMENT_CONTENT_LENGTH:
                log_warning(f"Comment too long: {len(content)} characters", request, {'post_id': post_id})
                return Response({
                    'success': False,
                    'message': f'Comment is too long (max {MAX_COMMENT_CONTENT_LENGTH} characters)'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            parent = None
            if parent_id:
                parent = Comment.objects.filter(id=parent_id, post=post).first()
            
            comment = Comment.objects.create(
                user=request.user,
                post=post,
                content=content,
                parent=parent
            )
            
            # Create notification
            if post.author != request.user:
                Notification.objects.create(
                    recipient=post.author,
                    sender=request.user,
                    notif_type='comment',
                    post=post,
                    comment=comment,
                    message=f'{request.user.username} commented on your post'
                )
            
            # If comment is a reply to another comment
            if parent and parent.user != request.user:
                Notification.objects.create(
                    recipient=parent.user,
                    sender=request.user,
                    notif_type='reply',
                    post=post,
                    comment=comment,
                    message=f'{request.user.username} replied to your comment'
                )
            
            log_info(f"User commented on post {post_id}", request, {
                'post_id': post_id,
                'comment_id': comment.id,
                'is_reply': parent is not None,
                'post_author': post.author.username
            })
            
            serializer = CommentSerializer(comment, context={'request': request})
            
            return Response({
                'success': True,
                'comment': serializer.data,
                'comments_count': post.comments.count()
            }, status=status.HTTP_201_CREATED)
    except Exception as e:
        log_error(f"Comment creation failed: {str(e)}", request, {'post_id': post_id})
        return Response({
            'success': False,
            'message': 'Failed to create comment'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _handle_comment_reaction(request, comment_id, reaction_type):
    """Helper function to handle comment reactions (like/dislike)"""
    try:
        with transaction.atomic():
            comment = get_object_or_404(Comment, id=comment_id)
            
            if comment.user == request.user:
                log_warning(f"User tried to {reaction_type} their own comment", request, {
                    'comment_id': comment_id,
                    'reaction_type': reaction_type
                })
                return {
                    'success': False,
                    'message': f'You cannot {reaction_type} your own comment'
                }, status.HTTP_400_BAD_REQUEST
            
            # Determine which field to work with
            target_field = comment.likes if reaction_type == 'like' else comment.dislikes
            opposite_field = comment.dislikes if reaction_type == 'like' else comment.likes
            
            # Check if user already has this reaction
            if target_field.filter(id=request.user.id).exists():
                # Remove reaction
                target_field.remove(request.user)
                action = f'un{reaction_type}d'
                log_info(f"User removed {reaction_type} from comment {comment_id}", request)
            else:
                # Remove opposite reaction if exists
                opposite_field.remove(request.user)
                # Add new reaction
                target_field.add(request.user)
                action = f'{reaction_type}d'
                
                # Create notification
                if comment.user != request.user:
                    notif_type = 'like_comment' if reaction_type == 'like' else 'dislike_comment'
                    Notification.objects.create(
                        recipient=comment.user,
                        sender=request.user,
                        notif_type=notif_type,
                        comment=comment,
                        message=f'{request.user.username} {reaction_type}d your comment'
                    )
                log_info(f"User {reaction_type}d comment {comment_id}", request, {
                    'comment_author': comment.user.username
                })
            
            # Get updated counts
            likes_count = comment.likes.count()
            dislikes_count = comment.dislikes.count()
            
            return {
                'success': True,
                'message': action.capitalize(),
                'likes_count': likes_count,
                'dislikes_count': dislikes_count,
                'is_liked': comment.likes.filter(id=request.user.id).exists(),
                'is_disliked': comment.dislikes.filter(id=request.user.id).exists()
            }, status.HTTP_200_OK
            
    except Exception as e:
        log_error(f"Comment reaction handling failed: {str(e)}", request, {
            'comment_id': comment_id,
            'reaction_type': reaction_type
        })
        return {
            'success': False,
            'message': 'Reaction operation failed'
        }, status.HTTP_500_INTERNAL_SERVER_ERROR


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def like_comment(request, comment_id):
    """Like/unlike a comment"""
    result, status_code = _handle_comment_reaction(request, comment_id, 'like')
    return Response(result, status=status_code)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def dislike_comment(request, comment_id):
    """Dislike/remove dislike from a comment"""
    result, status_code = _handle_comment_reaction(request, comment_id, 'dislike')
    return Response(result, status=status_code)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_comment(request, comment_id):
    """Delete a comment"""
    try:
        with transaction.atomic():
            comment = get_object_or_404(Comment, id=comment_id)
            
            if comment.user != request.user:
                log_warning(f"User attempted to delete another user's comment", request, {
                    'comment_id': comment_id,
                    'actual_owner': comment.user.username
                })
                return Response({
                    'success': False,
                    'message': 'You can only delete your own comments'
                }, status=status.HTTP_403_FORBIDDEN)
            
            post_id = comment.post.id
            comment.delete()
            
            log_audit(f"User deleted comment {comment_id}", request, {
                'comment_id': comment_id,
                'post_id': post_id
            })
            
            return Response({
                'success': True,
                'message': 'Comment deleted successfully'
            }, status=status.HTTP_200_OK)
    except Exception as e:
        log_error(f"Comment deletion failed: {str(e)}", request, {'comment_id': comment_id})
        return Response({
            'success': False,
            'message': 'Failed to delete comment'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_comment(request, comment_id):
    """Update a comment"""
    try:
        with transaction.atomic():
            comment = get_object_or_404(Comment, id=comment_id)
            
            if comment.user != request.user:
                log_warning(f"User attempted to edit another user's comment", request, {
                    'comment_id': comment_id,
                    'actual_owner': comment.user.username
                })
                return Response({
                    'success': False,
                    'message': 'You can only edit your own comments'
                }, status=status.HTTP_403_FORBIDDEN)
            
            content = request.data.get('content', '').strip()
            
            if not content:
                log_warning("Attempt to update comment with empty content", request)
                return Response({
                    'success': False,
                    'message': 'Comment content is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if len(content) > MAX_COMMENT_CONTENT_LENGTH:
                log_warning(f"Updated comment too long: {len(content)} characters", request)
                return Response({
                    'success': False,
                    'message': f'Comment is too long (max {MAX_COMMENT_CONTENT_LENGTH} characters)'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            old_content = comment.content
            comment.content = content
            comment.save()
            
            log_audit(f"User updated comment {comment_id}", request, {
                'comment_id': comment_id,
                'post_id': comment.post.id,
                'old_content_preview': old_content[:50] if old_content else None,
                'new_content_preview': content[:50]
            })
            
            serializer = CommentSerializer(comment, context={'request': request})
            
            return Response({
                'success': True,
                'message': 'Comment updated successfully',
                'comment': serializer.data
            }, status=status.HTTP_200_OK)
    except Exception as e:
        log_error(f"Comment update failed: {str(e)}", request, {'comment_id': comment_id})
        return Response({
            'success': False,
            'message': 'Failed to update comment'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)