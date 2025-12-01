from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.core.paginator import Paginator
import logging
import json
import mimetypes

import settings
from .models import Post, PostMedia, CategoryFormat
from .serializers import PostSerializer, PostMediaSerializer, CategoryFormatSerializer
from notifications.models import Notification

from interactions.models import Comment
from interactions.serializers import CommentSerializer
from accounts.serializers import UserSerializer

logger = logging.getLogger(__name__)

MAX_POST_CONTENT_LENGTH = 5000
MAX_MEDIA_FILE_SIZE = 10 * 1024 * 1024


# ════════════════════════════════════════════════════════════
# 📝 Post Endpoints
# ════════════════════════════════════════════════════════════

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def posts_list_create(request):
    """List all posts or create new post"""
    
    if request.method == 'GET':
        # Search parameters
        category = request.GET.get('category')
        username = request.GET.get('username')
        page = int(request.GET.get('page', 1))
        per_page = min(int(request.GET.get('per_page', 20)), 100)
        
        # Build query
        posts = Post.objects.filter(parent=None)
        
        if category:
            posts = posts.filter(category=category)
        
        if username:
            user = get_object_or_404(settings.AUTH_USER_MODEL, username=username)
            posts = posts.filter(author=user)
        
        # Optimize queries
        posts = posts.select_related('author').prefetch_related(
            'media', 'mentions', 'reactions', 'saved_by'
        ).order_by('-created_at')
        
        # Pagination
        paginator = Paginator(posts, per_page)
        try:
            posts_page = paginator.page(page)
        except:
            posts_page = paginator.page(1)
        
        serializer = PostSerializer(posts_page, many=True, context={'request': request})
        
        return Response({
            'success': True,
            'posts': serializer.data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': posts_page.has_next(),
                'has_previous': posts_page.has_previous(),
            }
        }, status=status.HTTP_200_OK)
    
    # POST - Create new post
    try:
        with transaction.atomic():
            content = request.data.get('content', '').strip()
            tags = request.data.get('tags', '').strip()
            mentions_raw = request.data.get('mentions', '').strip()
            parent_id = request.data.get('parent')
            category = request.data.get('category', '').strip()

            # Validation
            if not content and not request.FILES:
                return Response({
                    'success': False,
                    'message': 'Post content or media required'
                }, status=status.HTTP_400_BAD_REQUEST)

            if len(content) > MAX_POST_CONTENT_LENGTH:
                return Response({
                    'success': False,
                    'message': f'Post content is too long (max {MAX_POST_CONTENT_LENGTH} characters)'
                }, status=status.HTTP_400_BAD_REQUEST)

            parent = None
            if parent_id:
                parent = Post.objects.filter(id=parent_id).first()

            # Category is required for main posts
            if not parent and not category:
                return Response({
                    'success': False,
                    'message': 'Room/Category is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            post = Post.objects.create(
                author=request.user,
                content=content,
                tags=tags,
                parent=parent,
                category=category
            )

            # Handle mentions
            if mentions_raw:
                usernames = [u.strip() for u in mentions_raw.split(',') if u.strip()]
                mentioned_users = settings.AUTH_USER_MODEL.objects.filter(username__in=usernames)
                for mu in mentioned_users:
                    post.mentions.add(mu)
                    if mu != request.user:
                        Notification.objects.create(
                            recipient=mu,
                            sender=request.user,
                            notif_type='mention',
                            post=post,
                            message=f'{request.user.username} mentioned you in a post'
                        )

            # Handle media files
            for f in request.FILES.getlist('media'):
                # Validate file type
                ctype = f.content_type or mimetypes.guess_type(f.name)[0] or ''
                if ctype.startswith('image/'):
                    mtype = 'image'
                elif ctype.startswith('video/'):
                    mtype = 'video'
                elif ctype.startswith('audio/'):
                    mtype = 'audio'
                else:
                    mtype = 'file'
                
                # Validate file size
                if f.size > MAX_MEDIA_FILE_SIZE:
                    continue  # Skip large files
                    
                PostMedia.objects.create(post=post, file=f, media_type=mtype)

            serializer = PostSerializer(post, context={'request': request})
            return Response({
                'success': True,
                'post': serializer.data
            }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Post creation failed: {str(e)}")
        return Response({
            'success': False,
            'message': 'Failed to create post'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def post_detail(request, post_id):
    """Get single post details with comments and replies"""
    post = get_object_or_404(
        Post.objects.select_related('author')
        .prefetch_related('media', 'mentions', 'reactions', 'saved_by'),
        id=post_id
    )
    
    # Get post data
    post_serializer = PostSerializer(post, context={'request': request})
    data = post_serializer.data
    
    # Get comments with optimization
    comments = Comment.objects.filter(post=post).select_related('user').prefetch_related('likes').order_by('created_at')
    comment_serializer = CommentSerializer(comments, many=True, context={'request': request})
    data['comments'] = comment_serializer.data
    
    # Get replies with optimization
    replies = Post.objects.filter(parent=post).select_related('author').prefetch_related(
        'media', 'mentions', 'reactions'
    ).order_by('created_at')
    reply_serializer = PostSerializer(replies, many=True, context={'request': request})
    data['replies'] = reply_serializer.data
    
    return Response({
        'success': True,
        'post': data
    }, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_post(request, post_id):
    """Delete a post"""
    try:
        with transaction.atomic():
            post = get_object_or_404(Post, id=post_id)
            
            if post.author != request.user:
                return Response({
                    'success': False,
                    'message': 'You can only delete your own posts'
                }, status=status.HTTP_403_FORBIDDEN)
            
            post.delete()
            return Response({
                'success': True,
                'message': 'Post deleted successfully'
            }, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Post deletion failed: {str(e)}")
        return Response({
            'success': False,
            'message': 'Failed to delete post'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_post(request, post_id):
    """Update a post"""
    try:
        with transaction.atomic():
            post = get_object_or_404(Post, id=post_id)
            
            if post.author != request.user:
                return Response({
                    'success': False,
                    'message': 'You can only edit your own posts'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Use serializer for validation
            serializer = PostSerializer(post, data=request.data, partial=True, context={'request': request})
            
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'success': True,
                    'message': 'Post updated successfully',
                    'post': serializer.data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': 'Validation failed',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
    except Exception as e:
        logger.error(f"Post update failed: {str(e)}")
        return Response({
            'success': False,
            'message': 'Failed to update post'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def post_repost(request, post_id):
    """Repost a post"""
    try:
        with transaction.atomic():
            original_post = get_object_or_404(Post, id=post_id)
            
            # Check if user is reposting their own post
            if original_post.author == request.user:
                return Response({
                    'success': False,
                    'message': 'You cannot repost your own post'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if already reposted
            existing_repost = Post.objects.filter(
                author=request.user, 
                original_post=original_post,
                is_repost=True
            ).exists()
            
            if existing_repost:
                return Response({
                    'success': False,
                    'message': 'You have already reposted this post'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            new_post = Post.objects.create(
                author=request.user,
                content=original_post.content,
                is_repost=True,
                original_post=original_post,
                tags=original_post.tags,
                category=original_post.category
            )
            
            # Copy mentions
            for mu in original_post.mentions.all():
                new_post.mentions.add(mu)
            
            # Create notification
            Notification.objects.create(
                recipient=original_post.author,
                sender=request.user,
                notif_type='repost',
                post=original_post,
                message=f'{request.user.username} reposted your post'
            )
            
            serializer = PostSerializer(new_post, context={'request': request})
            
            return Response({
                'success': True,
                'post': serializer.data
            }, status=status.HTTP_201_CREATED)
    except Exception as e:
        logger.error(f"Repost failed: {str(e)}")
        return Response({
            'success': False,
            'message': 'Failed to repost'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def posts_by_category(request, category_id):
    """Get posts by category/room with pagination"""
    page = int(request.GET.get('page', 1))
    per_page = min(int(request.GET.get('per_page', 20)), 100)
    
    posts = Post.objects.filter(
        category=category_id,
        parent=None
    ).select_related('author').prefetch_related(
        'media', 'mentions', 'reactions'
    ).order_by('-created_at')
    
    paginator = Paginator(posts, per_page)
    try:
        posts_page = paginator.page(page)
    except:
        posts_page = paginator.page(1)
    
    serializer = PostSerializer(posts_page, many=True, context={'request': request})
    
    return Response({
        'success': True,
        'posts': serializer.data,
        'category': category_id,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count,
            'has_next': posts_page.has_next(),
            'has_previous': posts_page.has_previous(),
        }
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def user_posts(request, username):
    """Get posts by specific user with pagination"""
    user = get_object_or_404(settings.AUTH_USER_MODEL, username=username)
    
    page = int(request.GET.get('page', 1))
    per_page = min(int(request.GET.get('per_page', 20)), 100)
    
    posts = Post.objects.filter(
        author=user,
        parent=None
    ).select_related('author').prefetch_related(
        'media', 'mentions', 'reactions'
    ).order_by('-created_at')
    
    paginator = Paginator(posts, per_page)
    try:
        posts_page = paginator.page(page)
    except:
        posts_page = paginator.page(1)
    
    user_serializer = UserSerializer(user, context={'request': request})
    posts_serializer = PostSerializer(posts_page, many=True, context={'request': request})
    
    return Response({
        'success': True,
        'posts': posts_serializer.data,
        'username': username,
        'user': user_serializer.data,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count,
            'has_next': posts_page.has_next(),
            'has_previous': posts_page.has_previous(),
        }
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def post_thread(request, post_id):
    """Get post thread (post with all its replies)"""
    post = get_object_or_404(
        Post.objects.select_related('author').prefetch_related('media', 'mentions'),
        id=post_id
    )
    
    # Get post data
    post_serializer = PostSerializer(post, context={'request': request})
    data = post_serializer.data
    
    # Get replies with optimization
    replies = post.replies.select_related('author').prefetch_related(
        'media', 'mentions', 'reactions'
    ).order_by('created_at')
    replies_serializer = PostSerializer(replies, many=True, context={'request': request})
    data['replies'] = replies_serializer.data
    
    return Response({
        'success': True,
        'thread': data
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_post(request, post_id):
    """Save a post"""
    try:
        with transaction.atomic():
            post = get_object_or_404(Post, id=post_id)
            
            if post.saved_by.filter(id=request.user.id).exists():
                return Response({
                    'success': False,
                    'message': 'Post already saved'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            post.saved_by.add(request.user)
            
            return Response({
                'success': True,
                'message': 'Post saved successfully'
            }, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Save post failed: {str(e)}")
        return Response({
            'success': False,
            'message': 'Failed to save post'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unsave_post(request, post_id):
    """Unsave a post"""
    try:
        with transaction.atomic():
            post = get_object_or_404(Post, id=post_id)
            
            if not post.saved_by.filter(id=request.user.id).exists():
                return Response({
                    'success': False,
                    'message': 'Post not saved'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            post.saved_by.remove(request.user)
            
            return Response({
                'success': True,
                'message': 'Post unsaved successfully'
            }, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Unsave post failed: {str(e)}")
        return Response({
            'success': False,
            'message': 'Failed to unsave post'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def saved_posts(request):
    """Get user's saved posts with pagination"""
    page = int(request.GET.get('page', 1))
    per_page = min(int(request.GET.get('per_page', 20)), 100)
    
    saved_posts = request.user.saved_posts.filter(parent=None).select_related('author').prefetch_related(
        'media', 'mentions', 'reactions'
    ).order_by('-created_at')
    
    paginator = Paginator(saved_posts, per_page)
    try:
        saved_posts_page = paginator.page(page)
    except:
        saved_posts_page = paginator.page(1)
    
    serializer = PostSerializer(saved_posts_page, many=True, context={'request': request})
    
    return Response({
        'success': True,
        'posts': serializer.data,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count,
            'has_next': saved_posts_page.has_next(),
            'has_previous': saved_posts_page.has_previous(),
        }
    }, status=status.HTTP_200_OK)


# ════════════════════════════════════════════════════════════
# 📁 Category Format Endpoints
# ════════════════════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_category_format(request):
    """آپلود فایل فرمت برای یک دسته‌بندی (فقط سوپر یوزرها)"""
    if not request.user.is_superuser:
        return Response({
            'success': False,
            'message': 'Only superusers can upload format files'
        }, status=status.HTTP_403_FORBIDDEN)

    try:
        category = request.data.get('category', '').strip()
        format_file = request.FILES.get('format_file')

        if not category:
            return Response({
                'success': False,
                'message': 'Category is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not format_file:
            return Response({
                'success': False,
                'message': 'Format file is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # بررسی نوع فایل
        if not format_file.name.endswith('.json'):
            return Response({
                'success': False,
                'message': 'Only JSON files are allowed'
            }, status=status.HTTP_400_BAD_REQUEST)

        # بررسی valid بودن JSON
        try:
            format_file.seek(0)
            json.load(format_file)
            format_file.seek(0)  # بازگشت به ابتدای فایل
        except json.JSONDecodeError:
            return Response({
                'success': False,
                'message': 'Invalid JSON file'
            }, status=status.HTTP_400_BAD_REQUEST)

        # ایجاد یا آپدیت فرمت
        format_obj, created = CategoryFormat.objects.update_or_create(
            category=category,
            defaults={
                'format_file': format_file,
                'created_by': request.user
            }
        )

        serializer = CategoryFormatSerializer(format_obj, context={'request': request})
        
        return Response({
            'success': True,
            'message': 'Format uploaded successfully' if created else 'Format updated successfully',
            'format': serializer.data
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Format upload failed: {str(e)}")
        return Response({
            'success': False,
            'message': 'Failed to upload format'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_category_format(request, cat):
    """حذف فایل فرمت یک دسته‌بندی (فقط سوپر یوزرها)"""
    if not request.user.is_superuser:
        return Response({
            'success': False,
            'message': 'Only superusers can delete format files'
        }, status=status.HTTP_403_FORBIDDEN)

    try:
        format_obj = CategoryFormat.objects.filter(category=cat).first()
        
        if not format_obj:
            return Response({
                'success': False,
                'message': f'No format found for category: {cat}'
            }, status=status.HTTP_404_NOT_FOUND)

        format_obj.delete()
        
        return Response({
            'success': True,
            'message': 'Format deleted successfully'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Format deletion failed: {str(e)}")
        return Response({
            'success': False,
            'message': 'Failed to delete format'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_format(request, cat):
    """دریافت فایل فرمت برای یک دسته‌بندی (برای همه کاربران)"""
    try:
        format_obj = CategoryFormat.objects.filter(category=cat).first()
        
        if not format_obj or not format_obj.format_file:
            return Response({
                'success': False,
                'message': f'No format found for category: {cat}'
            }, status=status.HTTP_404_NOT_FOUND)

        # خواندن محتوای فایل JSON
        try:
            with open(format_obj.format_file.path, 'r', encoding='utf-8') as f:
                format_data = json.load(f)
        except Exception as e:
            logger.error(f"Error reading format file: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error reading format file'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            'success': True,
            'category': cat,
            'format': format_data,
            'last_updated': format_obj.updated_at
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Get format failed: {str(e)}")
        return Response({
            'success': False,
            'message': 'Failed to get format'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def get_format_data(cat):
    """تابع کمکی برای دریافت داده‌های فرمت از هر جای برنامه"""
    try:
        format_obj = CategoryFormat.objects.filter(category=cat).first()
        if format_obj and format_obj.format_file:
            with open(format_obj.format_file.path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    except Exception as e:
        logger.error(f"Error in get_format_data for {cat}: {str(e)}")
        return None


