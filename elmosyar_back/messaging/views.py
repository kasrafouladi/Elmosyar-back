from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.core.paginator import Paginator
from django.utils import timezone

import settings
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer

# جایگزین کردن لاگر قدیمی
from log_manager.log_config import log_info, log_error, log_warning, log_audit

MAX_MESSAGE_CONTENT_LENGTH = 2000


# ════════════════════════════════════════════════════════════
# 💬 Messaging Endpoints
# ════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def conversations_list(request):
    """Get user's conversations"""
    conversations = Conversation.objects.filter(participants=request.user).prefetch_related(
        'participants', 'messages'
    ).order_by('-updated_at')
    
    serializer = ConversationSerializer(conversations, many=True, context={'request': request})
    
    log_info(f"User viewed conversations list ({len(conversations)} conversations)", request)
    
    return Response({
        'success': True,
        'conversations': serializer.data,
        'count': len(conversations)
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_conversation(request, username):
    """Start a new conversation"""
    try:
        with transaction.atomic():
            other_user = get_object_or_404(settings.AUTH_USER_MODEL, username=username)
            
            if other_user == request.user:
                log_warning(f"User tried to start conversation with themselves", request)
                return Response({
                    'success': False,
                    'message': 'Cannot start conversation with yourself'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check for existing conversation
            conversation = Conversation.objects.filter(participants=request.user).filter(
                participants=other_user
            ).first()
            
            if not conversation:
                conversation = Conversation.objects.create()
                conversation.participants.add(request.user, other_user)
                log_audit(f"User started new conversation with {username}", request, {
                    'other_user_id': other_user.id,
                    'conversation_id': conversation.id
                })
            else:
                log_info(f"User accessed existing conversation with {username}", request, {
                    'conversation_id': conversation.id
                })
            
            serializer = ConversationSerializer(conversation, context={'request': request})
            
            return Response({
                'success': True,
                'conversation': serializer.data,
                'message': 'Conversation started successfully'
            }, status=status.HTTP_200_OK)
    except Exception as e:
        log_error(f"Start conversation failed: {str(e)}", request, {'target_user': username})
        return Response({
            'success': False,
            'message': 'Failed to start conversation'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def conversation_detail(request, conversation_id):
    """Get conversation messages with pagination"""
    conversation = get_object_or_404(
        Conversation.objects.prefetch_related('participants', 'messages'),
        id=conversation_id, 
        participants=request.user
    )
    
    page = int(request.GET.get('page', 1))
    per_page = min(int(request.GET.get('per_page', 50)), 100)
    
    # Mark messages as read
    unread_count = conversation.messages.filter(is_read=False).exclude(sender=request.user).count()
    conversation.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
    
    messages = conversation.messages.all().order_by('-created_at')
    paginator = Paginator(messages, per_page)
    
    try:
        messages_page = paginator.page(page)
    except:
        messages_page = paginator.page(1)
    
    log_info(f"User viewed conversation {conversation_id} page {page}, marked {unread_count} messages as read", request)
    
    conversation_serializer = ConversationSerializer(conversation, context={'request': request})
    message_serializer = MessageSerializer(messages_page, many=True, context={'request': request})
    
    return Response({
        'success': True,
        'conversation': conversation_serializer.data,
        'messages': message_serializer.data,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count,
            'has_next': messages_page.has_next(),
            'has_previous': messages_page.has_previous(),
        }
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_message(request, conversation_id):
    """Send a message in conversation"""
    try:
        with transaction.atomic():
            conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
            
            content = request.data.get('content', '').strip()
            image = request.FILES.get('image')
            file = request.FILES.get('file')
            
            if not content and not image and not file:
                log_warning("Attempt to send empty message", request)
                return Response({
                    'success': False,
                    'message': 'Message content or file is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if content and len(content) > MAX_MESSAGE_CONTENT_LENGTH:
                log_warning(f"Message too long: {len(content)} characters", request)
                return Response({
                    'success': False,
                    'message': f'Message is too long (max {MAX_MESSAGE_CONTENT_LENGTH} characters)'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            message = Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content,
                image=image,
                file=file
            )
            
            # Update conversation time
            conversation.updated_at = timezone.now()
            conversation.save()
            
            # لاگ پیام ارسالی (محتوا را کوتاه می‌کنیم)
            truncated_content = content[:100] + "..." if len(content) > 100 else content
            log_info(f"User sent message in conversation {conversation_id}", request, {
                'conversation_id': conversation_id,
                'message_id': message.id,
                'has_image': bool(image),
                'has_file': bool(file),
                'content_preview': truncated_content
            })
            
            serializer = MessageSerializer(message, context={'request': request})
            
            return Response({
                'success': True,
                'message': serializer.data
            }, status=status.HTTP_201_CREATED)
    except Exception as e:
        log_error(f"Send message failed: {str(e)}", request, {
            'conversation_id': conversation_id,
            'has_content': bool(content),
            'has_image': bool(image),
            'has_file': bool(file)
        })
        return Response({
            'success': False,
            'message': 'Failed to send message'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_message(request, message_id):
    """Delete a message"""
    try:
        with transaction.atomic():
            message = get_object_or_404(Message, id=message_id)
            
            if message.sender != request.user:
                log_warning(f"User attempted to delete another user's message", request, {
                    'message_id': message_id,
                    'actual_sender': message.sender.username
                })
                return Response({
                    'success': False,
                    'message': 'You can only delete your own messages'
                }, status=status.HTTP_403_FORBIDDEN)
            
            conversation_id = message.conversation.id
            message_content = message.content[:50] if message.content else "No content"
            message.delete()
            
            log_audit(f"User deleted message from conversation {conversation_id}", request, {
                'message_id': message_id,
                'conversation_id': conversation_id,
                'content_preview': message_content
            })
            
            return Response({
                'success': True,
                'message': 'Message deleted successfully'
            }, status=status.HTTP_200_OK)
    except Exception as e:
        log_error(f"Message deletion failed: {str(e)}", request, {'message_id': message_id})
        return Response({
            'success': False,
            'message': 'Failed to delete message'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_message(request, message_id):
    """Update a message"""
    try:
        with transaction.atomic():
            message = get_object_or_404(Message, id=message_id)
            
            if message.sender != request.user:
                log_warning(f"User attempted to edit another user's message", request, {
                    'message_id': message_id,
                    'actual_sender': message.sender.username
                })
                return Response({
                    'success': False,
                    'message': 'You can only edit your own messages'
                }, status=status.HTTP_403_FORBIDDEN)
            
            content = request.data.get('content', '').strip()
            
            if not content:
                log_warning("Attempt to update message with empty content", request)
                return Response({
                    'success': False,
                    'message': 'Message content is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if len(content) > MAX_MESSAGE_CONTENT_LENGTH:
                log_warning(f"Updated message too long: {len(content)} characters", request)
                return Response({
                    'success': False,
                    'message': f'Message is too long (max {MAX_MESSAGE_CONTENT_LENGTH} characters)'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            old_content = message.content
            message.content = content
            message.save()
            
            log_audit(f"User updated message {message_id}", request, {
                'message_id': message_id,
                'conversation_id': message.conversation.id,
                'old_content_preview': old_content[:50] if old_content else None,
                'new_content_preview': content[:50]
            })
            
            serializer = MessageSerializer(message, context={'request': request})
            
            return Response({
                'success': True,
                'message': 'Message updated successfully',
                'message_data': serializer.data
            }, status=status.HTTP_200_OK)
    except Exception as e:
        log_error(f"Message update failed: {str(e)}", request, {'message_id': message_id})
        return Response({
            'success': False,
            'message': 'Failed to update message'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)