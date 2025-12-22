from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
import json
import mimetypes
import re

import settings
from .models import Post, PostMedia, CategoryFormat
from .serializers import PostSerializer, PostMediaSerializer, CategoryFormatSerializer
from notifications.models import Notification

from interactions.models import Comment
from interactions.serializers import CommentSerializer
from accounts.serializers import UserSerializer

# جایگزین کردن لاگر قدیمی
from log_manager.log_config import log_info, log_error, log_warning, log_audit, log_api_request

MAX_POST_CONTENT_LENGTH = 5000
MAX_MEDIA_FILE_SIZE = 10 * 1024 * 1024


# ════════════════════════════════════════════════════════════
# 🛠️ Helper Functions
# ════════════════════════════════════════════════════════════

def apply_advanced_search_filter(queryset, search_json, category):
    """
    اعمال فیلترهای پیشرفته بر اساس JSON جستجو و فرمت دسته‌بندی
    این تابع از Regex هم برای کلیدها و هم برای مقادیر پشتیبانی می‌کند
    """
    try:
        search_criteria = json.loads(search_json)
        
        # بررسی اینکه search_criteria یک دیکشنری است
        if not isinstance(search_criteria, dict):
            raise ValidationError('Search criteria must be a JSON object')
        
        # اگر دسته‌بندی مشخص نشده، خطا برگردان
        if not category:
            raise ValidationError('Category is required for advanced search')
        
        # دریافت فرمت JSON مربوط به این دسته‌بندی
        format_obj = CategoryFormat.objects.filter(category=category).first()
        
        if not format_obj:
            raise ValidationError(f'No format found for category: {category}')
        
        # خواندن فرمت JSON از فایل
        try:
            with open(format_obj.format_file.path, 'r', encoding='utf-8') as f:
                format_data = json.load(f)
        except Exception as e:
            log_error(f"Error reading format file: {str(e)}")
            raise ValidationError('Error reading format file')
        
        format_keys = format_data.keys()

        not_empty = True

        matching_keys = {}

        for key_regex in search_criteria.keys():
            # یافتن کلیدهای post_attributes که با key_regex مطابقت دارند
            matching_keys[key_regex] = []
            for attr_key in format_keys:
                try:
                    if re.match(key_regex, attr_key):
                        matching_keys[key_regex].append(attr_key)
                except re.error:
                    log_error(f"Invalid regex pattern for key matching: {key_regex}")
                    break
            if matching_keys[key_regex] == []:
                not_empty = False
                break
        
        if not not_empty:
            log_info(f"Advanced search applied: 0 posts matched", None, {
            'category': category,
            'search_criteria': search_criteria,
            'matched_posts': 0
            })
            return queryset.filter(id__in=[])

        filtered_posts = []
        for post in queryset:
            post_attributes = post.attributes or {}
            match_all_criteria = True
                
            for regex_key, possible_keys in matching_keys.items():
                match_all_criteria = False
                for key in possible_keys:
                    if re.match(search_criteria[regex_key], post_attributes[key]):
                        match_all_criteria = True
                        break
                if not match_all_criteria:
                    break
            
            if match_all_criteria:
                filtered_posts.append(post.id)
        
        log_info(f"Advanced search applied: {len(filtered_posts)} posts matched", None, {
            'category': category,
            'search_criteria': search_criteria,
            'matched_posts': len(filtered_posts)
        })
        
        # فیلتر کردن پست‌ها بر اساس IDهای فیلتر شده
        return queryset.filter(id__in=filtered_posts)
        
    except json.JSONDecodeError:
        log_warning(f"Invalid JSON in advanced search: {search_json}")
        raise ValidationError('Invalid JSON in search parameter')
    except ValidationError as e:
        log_warning(f"Advanced search validation error: {str(e)}")
        raise e
    except Exception as e:
        log_error(f"Advanced search error: {str(e)}")
        raise ValidationError('Error in advanced search')


def validate_post_attributes(attributes, category):
    """
    اعتبارسنجی attributes پست بر اساس فرمت دسته‌بندی
    """
    if not attributes or not category:
        return True, None
    
    format_obj = CategoryFormat.objects.filter(category=category).first()
    if not format_obj:
        return True, None  # اگر فرمتی وجود ندارد، اعتبارسنجی نکن
    
    try:
        with open(format_obj.format_file.path, 'r', encoding='utf-8') as f:
            format_data = json.load(f)
        
        for key, value in attributes.items():
            if key in format_data:
                # اعتبارسنجی با regex فرمت
                if not re.match(format_data[key], str(value)):
                    log_warning(f"Attribute validation failed: {key}={value} doesn't match pattern")
                    return False, f'Attribute "{key}" does not match format pattern'
        
        return True, None
    except Exception as e:
        log_error(f"Format validation error: {str(e)}", None, {'category': category})
        return False, f'Error validating format: {str(e)}'


def validate_post_update_attributes(post, attributes, category):
    """
    اعتبارسنجی attributes برای به‌روزرسانی پست
    """

    if not category:
        return True, None
    
    format_obj = CategoryFormat.objects.filter(category=category).first()
    if not format_obj:
        return True, None
    
    try:
        with open(format_obj.format_file.path, 'r', encoding='utf-8') as f:
            format_data = json.load(f)
        
        # اگر attributes جدید ارسال شده

        if attributes is not None:
            post_attributes = post.attributes or {}
            merged_attributes = {**post_attributes, **attributes}
            
            for key, value in merged_attributes.items():
                if key in format_data:
                    # اعتبارسنجی با regex فرمت
                    if not re.match(format_data[key], str(value)):
                        log_warning(f"Update attribute validation failed: {key}={value}")
                        return False, f'Attribute "{key}" does not match format pattern'
            
            # بررسی کلیدهای اجباری در فرمت
            for key, pattern in format_data.items():
                if key not in merged_attributes:
                    log_warning(f"Required attribute missing: {key}")
                    return False, f'Attribute "{key}" is required and cannot be removed'
        
        return True, None
    except Exception as e:
        log_error(f"Format validation error for update: {str(e)}", None, {
            'post_id': post.id,
            'category': category
        })
        return False, f'Error validating format: {str(e)}'


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
        search_json = request.GET.get('search')
        page = int(request.GET.get('page', 1))
        per_page = min(int(request.GET.get('per_page', 20)), 100)

        # Build query
        posts = Post.objects.all()
        
        if category:
            posts = posts.filter(category=category)
        
        if username:
            user = get_object_or_404(settings.AUTH_USER_MODEL, username=username)
            posts = posts.filter(author=user)
        
        # اگر پارامتر search وجود داشت، فیلترهای پیشرفته را اعمال کن
        if search_json:
            try:
                posts = apply_advanced_search_filter(posts, search_json, category)
            except ValidationError as e:
                log_warning(f"Advanced search validation error: {str(e)}", request)
                return Response({
                    'success': False,
                    'message': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        
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
        
        log_api_request(f"Posts list retrieved", request, {
            'category': category,
            'username': username,
            'has_search': bool(search_json),
            'page': page,
            'per_page': per_page,
            'total_posts': paginator.count
        })
        
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
            attributes = request.data.get('attributes', {})

            # Validation
            if not content and not request.FILES and not attributes:
                log_warning("Post creation attempt without content, media or attributes", request)
                return Response({
                    'success': False,
                    'message': 'Post content, media or attributes required'
                }, status=status.HTTP_400_BAD_REQUEST)

            if len(content) > MAX_POST_CONTENT_LENGTH:
                log_warning(f"Post content too long: {len(content)} characters", request, {
                    'max_allowed': MAX_POST_CONTENT_LENGTH
                })
                return Response({
                    'success': False,
                    'message': f'Post content is too long (max {MAX_POST_CONTENT_LENGTH} characters)'
                }, status=status.HTTP_400_BAD_REQUEST)

            parent = None
            if parent_id:
                parent = Post.objects.filter(id=parent_id).first()

            # Category is required for main posts
            if not parent and not category:
                log_warning("Post creation without category for main post", request)
                return Response({
                    'success': False,
                    'message': 'Category is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            # اعتبارسنجی attributes بر اساس فرمت دسته‌بندی
            if attributes and category:
                
                # تبدیل attributes از string به dictionary اگر لازم باشد
                if attributes and isinstance(attributes, str):
                    try:
                        attributes = json.loads(attributes)
                    except json.JSONDecodeError:
                        log_warning(f"Invalid JSON in attributes string")
                    return False, 'Attributes must be valid JSON'
                
                is_valid, error_message = validate_post_attributes(attributes, category)
                if not is_valid:
                    log_warning(f"Post attributes validation failed: {error_message}", request, {
                        'category': category,
                        'attributes': attributes
                    })
                    return Response({
                        'success': False,
                        'message': error_message
                    }, status=status.HTTP_400_BAD_REQUEST)

            post = Post.objects.create(
                author=request.user,
                content=content,
                tags=tags,
                parent=parent,
                category=category,
                attributes=attributes
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
                log_info(f"Post mentions added: {len(mentioned_users)} users", request, {
                    'mentioned_users': usernames
                })

            # Handle media files
            media_files = []
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
                    log_warning(f"Media file too large: {f.size} bytes, skipping", request, {
                        'filename': f.name,
                        'max_allowed': MAX_MEDIA_FILE_SIZE
                    })
                    continue  # Skip large files
                    
                PostMedia.objects.create(post=post, file=f, media_type=mtype)
                media_files.append({
                    'filename': f.name,
                    'size': f.size,
                    'type': mtype
                })

            log_audit(f"Post created successfully", request, {
                'post_id': post.id,
                'category': category,
                'has_media': len(media_files) > 0,
                'media_count': len(media_files),
                'has_parent': parent is not None,
                'parent_id': parent.id if parent else None,
                'has_attributes': bool(attributes),
                'content_length': len(content)
            })

            serializer = PostSerializer(post, context={'request': request})
            return Response({
                'success': True,
                'post': serializer.data
            }, status=status.HTTP_201_CREATED)

    except Exception as e:
        log_error(f"Post creation failed: {str(e)}", request, {
            'category': category if 'category' in locals() else None,
            'has_media': bool(request.FILES)
        })
        return Response({
            'success': False,
            'message': 'Failed to create post'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def post_detail(request, post_id):
    """Get single post details with comments and replies"""
    try:
        post = get_object_or_404(
            Post.objects.select_related('author')
            .prefetch_related('media', 'mentions', 'reactions', 'saved_by'),
            id=post_id
        )
        
        log_info(f"Post details viewed", request, {
            'post_id': post_id,
            'author': post.author.username,
            'category': post.category
        })
        
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
    except Exception as e:
        log_error(f"Post detail retrieval failed: {str(e)}", request, {'post_id': post_id})
        return Response({
            'success': False,
            'message': 'Failed to get post details'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_post(request, post_id):
    """Delete a post"""
    try:
        with transaction.atomic():
            post = get_object_or_404(Post, id=post_id)
            
            if post.author != request.user:
                log_warning(f"User attempted to delete another user's post", request, {
                    'post_id': post_id,
                    'post_author': post.author.username
                })
                return Response({
                    'success': False,
                    'message': 'You can only delete your own posts'
                }, status=status.HTTP_403_FORBIDDEN)
            
            post_category = post.category
            post_author = post.author.username
            has_media = post.media.exists()
            
            post.delete()
            
            log_audit(f"Post deleted", request, {
                'post_id': post_id,
                'category': post_category,
                'author': post_author,
                'had_media': has_media
            })
            
            return Response({
                'success': True,
                'message': 'Post deleted successfully'
            }, status=status.HTTP_200_OK)
    except Exception as e:
        log_error(f"Post deletion failed: {str(e)}", request, {'post_id': post_id})
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
                log_warning(f"User attempted to edit another user's post", request, {
                    'post_id': post_id,
                    'post_author': post.author.username
                })
                return Response({
                    'success': False,
                    'message': 'You can only edit your own posts'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # دریافت داده‌های به‌روزرسانی
            content = request.data.get('content')
            tags = request.data.get('tags')
            category = request.data.get('category')
            attributes = request.data.get('attributes')
            
            # اعتبارسنجی attributes بر اساس فرمت دسته‌بندی
            if category or post.category:
                current_category = category or post.category
                is_valid, error_message = validate_post_update_attributes(post, attributes, current_category)
                if not is_valid:
                    log_warning(f"Post update validation failed: {error_message}", request, {
                        'post_id': post_id,
                        'category': current_category
                    })
                    return Response({
                        'success': False,
                        'message': error_message
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Use serializer for validation
            serializer = PostSerializer(post, data=request.data, partial=True, context={'request': request})
            
            if serializer.is_valid():
                old_content = post.content
                old_category = post.category
                
                serializer.save()
                
                changes = {}
                if content and content != old_content:
                    changes['content_changed'] = True
                if category and category != old_category:
                    changes['category_changed'] = True
                if attributes:
                    changes['attributes_updated'] = True
                
                log_audit(f"Post updated", request, {
                    'post_id': post_id,
                    **changes,
                    'new_category': category or post.category
                })
                
                return Response({
                    'success': True,
                    'message': 'Post updated successfully',
                    'post': serializer.data
                }, status=status.HTTP_200_OK)
            else:
                log_warning(f"Post update validation failed", request, {
                    'post_id': post_id,
                    'errors': serializer.errors
                })
                return Response({
                    'success': False,
                    'message': 'Validation failed',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
    except Exception as e:
        log_error(f"Post update failed: {str(e)}", request, {'post_id': post_id})
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
                log_warning(f"User attempted to repost their own post", request, {'post_id': post_id})
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
                log_warning(f"User attempted to repost same post again", request, {'post_id': post_id})
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
                category=original_post.category,
                attributes=original_post.attributes  # کپی کردن attributes
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
            
            log_audit(f"Post reposted", request, {
                'original_post_id': post_id,
                'repost_id': new_post.id,
                'original_author': original_post.author.username,
                'category': original_post.category
            })
            
            serializer = PostSerializer(new_post, context={'request': request})
            
            return Response({
                'success': True,
                'post': serializer.data
            }, status=status.HTTP_201_CREATED)
    except Exception as e:
        log_error(f"Repost failed: {str(e)}", request, {'post_id': post_id})
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
    
    log_api_request(f"Posts by category viewed", request, {
        'category': category_id,
        'page': page,
        'per_page': per_page,
        'total_posts': paginator.count
    })
    
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
    
    log_api_request(f"User posts viewed", request, {
        'target_user': username,
        'page': page,
        'per_page': per_page,
        'total_posts': paginator.count
    })
    
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
    try:
        post = get_object_or_404(
            Post.objects.select_related('author').prefetch_related('media', 'mentions'),
            id=post_id
        )
        
        log_api_request(f"Post thread viewed", request, {
            'post_id': post_id,
            'author': post.author.username,
            'category': post.category
        })
        
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
    except Exception as e:
        log_error(f"Post thread retrieval failed: {str(e)}", request, {'post_id': post_id})
        return Response({
            'success': False,
            'message': 'Failed to get post thread'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_post(request, post_id):
    """Save a post"""
    try:
        with transaction.atomic():
            post = get_object_or_404(Post, id=post_id)
            
            if post.saved_by.filter(id=request.user.id).exists():
                log_warning(f"User attempted to save already saved post", request, {'post_id': post_id})
                return Response({
                    'success': False,
                    'message': 'Post already saved'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            post.saved_by.add(request.user)
            
            log_audit(f"Post saved", request, {
                'post_id': post_id,
                'author': post.author.username,
                'category': post.category
            })
            
            return Response({
                'success': True,
                'message': 'Post saved successfully'
            }, status=status.HTTP_200_OK)
    except Exception as e:
        log_error(f"Save post failed: {str(e)}", request, {'post_id': post_id})
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
                log_warning(f"User attempted to unsave non-saved post", request, {'post_id': post_id})
                return Response({
                    'success': False,
                    'message': 'Post not saved'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            post.saved_by.remove(request.user)
            
            log_audit(f"Post unsaved", request, {
                'post_id': post_id,
                'author': post.author.username,
                'category': post.category
            })
            
            return Response({
                'success': True,
                'message': 'Post unsaved successfully'
            }, status=status.HTTP_200_OK)
    except Exception as e:
        log_error(f"Unsave post failed: {str(e)}", request, {'post_id': post_id})
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
    
    log_info(f"Saved posts viewed", request, {
        'page': page,
        'per_page': per_page,
        'total_saved': paginator.count
    })
    
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
        log_warning(f"Non-superuser attempted to upload format file", request)
        return Response({
            'success': False,
            'message': 'Only superusers can upload format files'
        }, status=status.HTTP_403_FORBIDDEN)

    try:
        category = request.data.get('category', '').strip()
        format_file = request.FILES.get('format_file')

        if not category:
            log_warning(f"Format upload without category", request)
            return Response({
                'success': False,
                'message': 'Category is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not format_file:
            log_warning(f"Format upload without file", request)
            return Response({
                'success': False,
                'message': 'Format file is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # بررسی نوع فایل
        if not format_file.name.endswith('.json'):
            log_warning(f"Non-JSON file upload attempt: {format_file.name}", request)
            return Response({
                'success': False,
                'message': 'Only JSON files are allowed'
            }, status=status.HTTP_400_BAD_REQUEST)

        # بررسی valid بودن JSON
        try:
            format_file.seek(0)
            format_data = json.load(format_file)
            format_file.seek(0)  # بازگشت به ابتدای فایل
        except json.JSONDecodeError as e:
            log_warning(f"Invalid JSON file: {str(e)}", request)
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

        log_audit(f"Category format uploaded/updated", request, {
            'category': category,
            'created': created,
            'format_id': format_obj.id,
            'file_size': format_file.size,
            'keys_count': len(format_data.keys()) if format_data else 0
        })

        serializer = CategoryFormatSerializer(format_obj, context={'request': request})
        
        return Response({
            'success': True,
            'message': 'Format uploaded successfully' if created else 'Format updated successfully',
            'format': serializer.data
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        log_error(f"Format upload failed: {str(e)}", request)
        # Return detailed error when in DEBUG to aid debugging; keep generic otherwise
        detail = str(e) if getattr(settings, 'DEBUG', False) else 'Failed to upload format'
        return Response({
            'success': False,
            'message': 'Failed to upload format',
            'error': detail
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_category_format(request, cat):
    """حذف فایل فرمت یک دسته‌بندی (فقط سوپر یوزرها)"""
    if not request.user.is_superuser:
        log_warning(f"Non-superuser attempted to delete format file", request, {'category': cat})
        return Response({
            'success': False,
            'message': 'Only superusers can delete format files'
        }, status=status.HTTP_403_FORBIDDEN)

    try:
        format_obj = CategoryFormat.objects.filter(category=cat).first()
        
        if not format_obj:
            log_warning(f"Attempt to delete non-existent format", request, {'category': cat})
            return Response({
                'success': False,
                'message': f'No format found for category: {cat}'
            }, status=status.HTTP_404_NOT_FOUND)

        format_obj.delete()
        
        log_audit(f"Category format deleted", request, {'category': cat})
        
        return Response({
            'success': True,
            'message': 'Format deleted successfully'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        log_error(f"Format deletion failed: {str(e)}", request, {'category': cat})
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
            log_warning(f"Format requested for non-existent category", request, {'category': cat})
            return Response({
                'success': False,
                'message': f'No format found for category: {cat}'
            }, status=status.HTTP_404_NOT_FOUND)

        # خواندن محتوای فایل JSON
        try:
            with open(format_obj.format_file.path, 'r', encoding='utf-8') as f:
                format_data = json.load(f)
        except Exception as e:
            log_error(f"Error reading format file: {str(e)}", request, {'category': cat})
            return Response({
                'success': False,
                'message': 'Error reading format file'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        log_info(f"Format file retrieved", request, {
            'category': cat,
            'keys_count': len(format_data.keys()) if format_data else 0,
            'last_updated': format_obj.updated_at
        })

        return Response({
            'success': True,
            'category': cat,
            'format': format_data,
            'last_updated': format_obj.updated_at
        }, status=status.HTTP_200_OK)

    except Exception as e:
        log_error(f"Get format failed: {str(e)}", request, {'category': cat})
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
        log_error(f"Error in get_format_data for {cat}: {str(e)}")
        return None