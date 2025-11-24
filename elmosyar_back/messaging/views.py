from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.core.paginator import Paginator
from django.utils import timezone
import logging

from accounts.models import User
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer

logger = logging.getLogger(__name__)

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
            other_user = get_object_or_404(User, username=username)
            
            if other_user == request.user:
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
            
            serializer = ConversationSerializer(conversation, context={'request': request})
            
            return Response({
                'success': True,
                'conversation': serializer.data,
                'message': 'Conversation started successfully'
            }, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Start conversation failed: {str(e)}")
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
    conversation.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
    
    messages = conversation.messages.all().order_by('-created_at')
    paginator = Paginator(messages, per_page)
    
    try:
        messages_page = paginator.page(page)
    except:
        messages_page = paginator.page(1)
    
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
                return Response({
                    'success': False,
                    'message': 'Message content or file is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if content and len(content) > MAX_MESSAGE_CONTENT_LENGTH:
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
            
            serializer = MessageSerializer(message, context={'request': request})
            
            return Response({
                'success': True,
                'message': serializer.data
            }, status=status.HTTP_201_CREATED)
    except Exception as e:
        logger.error(f"Send message failed: {str(e)}")
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
                return Response({
                    'success': False,
                    'message': 'You can only delete your own messages'
                }, status=status.HTTP_403_FORBIDDEN)
            
            message.delete()
            return Response({
                'success': True,
                'message': 'Message deleted successfully'
            }, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Message deletion failed: {str(e)}")
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
                return Response({
                    'success': False,
                    'message': 'You can only edit your own messages'
                }, status=status.HTTP_403_FORBIDDEN)
            
            content = request.data.get('content', '').strip()
            
            if not content:
                return Response({
                    'success': False,
                    'message': 'Message content is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if len(content) > MAX_MESSAGE_CONTENT_LENGTH:
                return Response({
                    'success': False,
                    'message': f'Message is too long (max {MAX_MESSAGE_CONTENT_LENGTH} characters)'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            message.content = content
            message.save()
            
            serializer = MessageSerializer(message, context={'request': request})
            
            return Response({
                'success': True,
                'message': 'Message updated successfully',
                'message_data': serializer.data
            }, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Message update failed: {str(e)}")
        return Response({
            'success': False,
            'message': 'Failed to update message'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)