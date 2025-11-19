from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from django.db.models import Q, Count
from django.core.paginator import Paginator
import json
from datetime import timedelta
import mimetypes

from .models import User, Post, PostMedia, Comment, Notification, Reaction, Conversation, Message


# ════════════════════════════════════════════════════════════
# 🔧 Helper Functions
# ════════════════════════════════════════════════════════════

def serialize_user(user, include_sensitive=False, current_user=None):
    """سریالایز کردن اطلاعات کاربر"""
    data = {
        'id': user.id,
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'profile_picture': user.profile_picture.url if user.profile_picture else None,
        'bio': user.bio,
        'student_id': user.student_id,
        'followers_count': user.followers_count,
        'following_count': user.following_count,
        'posts_count': user.posts_count,
    }
    
    if include_sensitive:
        data.update({
            'email': user.email,
            'is_email_verified': user.is_email_verified,
            'created_at': user.created_at.isoformat(),
        })
    
    # اضافه کردن وضعیت فالو برای کاربر جاری
    if current_user and current_user.is_authenticated:
        data['is_following'] = current_user.following.filter(id=user.id).exists()
        data['is_me'] = current_user.id == user.id
    
    return data


def serialize_post(post, include_user_info=True, current_user=None):
    """سریالایز کردن اطلاعات پست"""
    media_list = []
    for m in post.media.all():
        media_list.append({
            'id': m.id,
            'url': m.file.url if m.file else '',
            'type': m.media_type,
            'caption': m.caption,
        })
    
    data = {
        'id': post.id,
        'author': post.author.username,
        'content': post.content,
        'created_at': post.created_at.isoformat(),
        'updated_at': post.updated_at.isoformat(),
        'tags': [t.strip() for t in post.tags.split(',')] if post.tags else [],
        'mentions': [serialize_user(u) for u in post.mentions.all()],
        'media': media_list,
        'likes_count': post.likes_count,
        'dislikes_count': post.dislikes_count,
        'comments_count': post.comments_count,
        'reposts_count': post.reposts.count(),
        'replies_count': post.replies.count(),
        'is_repost': post.is_repost,
        'original_post_id': post.original_post.id if post.original_post else None,
        'parent_id': post.parent.id if post.parent else None,
        'category': post.category or '',
    }
    
    if include_user_info:
        data['author_info'] = serialize_user(post.author, include_sensitive=False, current_user=current_user)
    
    # اضافه کردن وضعیت ری‌اکشن کاربر جاری
    if current_user and current_user.is_authenticated:
        user_reaction = post.reactions.filter(user=current_user).first()
        data['user_reaction'] = user_reaction.reaction if user_reaction else None
        data['is_saved'] = post.saved_by.filter(id=current_user.id).exists()
    
    return data


def serialize_comment(comment, current_user=None):
    """سریالایز کردن اطلاعات کامنت"""
    data = {
        'id': comment.id,
        'user': comment.user.username,
        'user_info': serialize_user(comment.user, include_sensitive=False, current_user=current_user),
        'content': comment.content,
        'created_at': comment.created_at.isoformat(),
        'parent_id': comment.parent.id if comment.parent else None,
        'likes_count': comment.likes_count,
        'replies_count': comment.replies_count,
    }
    
    if current_user and current_user.is_authenticated:
        data['is_liked'] = comment.likes.filter(id=current_user.id).exists()
    
    return data


def serialize_notification(notification):
    """سریالایز کردن اطلاعات نوتیفیکیشن"""
    return {
        'id': notification.id,
        'sender': notification.sender.username,
        'sender_info': serialize_user(notification.sender, include_sensitive=False),
        'type': notification.notif_type,
        'post_id': notification.post.id if notification.post else None,
        'comment_id': notification.comment.id if notification.comment else None,
        'message': notification.message,
        'is_read': notification.is_read,
        'created_at': notification.created_at.isoformat(),
    }


def serialize_conversation(conversation, current_user):
    """سریالایز کردن اطلاعات مکالمه"""
    other_user = conversation.participants.exclude(id=current_user.id).first()
    last_message = conversation.messages.last()
    
    return {
        'id': conversation.id,
        'other_user': serialize_user(other_user, include_sensitive=False) if other_user else None,
        'last_message': {
            'content': last_message.content[:100] + '...' if last_message and len(last_message.content) > 100 else last_message.content if last_message else '',
            'sender': last_message.sender.username if last_message else '',
            'created_at': last_message.created_at.isoformat() if last_message else None,
            'is_read': last_message.is_read if last_message else True,
        } if last_message else None,
        'unread_count': conversation.messages.filter(is_read=False).exclude(sender=current_user).count(),
        'updated_at': conversation.updated_at.isoformat(),
    }


def serialize_message(message):
    """سریالایز کردن اطلاعات پیام"""
    return {
        'id': message.id,
        'sender': serialize_user(message.sender, include_sensitive=False),
        'content': message.content,
        'image': message.image.url if message.image else None,
        'file': {
            'url': message.file.url if message.file else None,
            'name': message.file.name.split('/')[-1] if message.file else None,
        } if message.file else None,
        'is_read': message.is_read,
        'created_at': message.created_at.isoformat(),
    }


# ════════════════════════════════════════════════════════════
# 🏠 Basic Endpoint
# ════════════════════════════════════════════════════════════

@require_http_methods(["GET"])
def index(request):
    """API root endpoint"""
    return JsonResponse({
        'success': True,
        'message': 'API is running',
        'endpoints': {
            'auth': {
                'signup': '/api/signup/',
                'login': '/api/login/',
                'logout': '/api/logout/',
                'verify_email': '/api/verify-email/{token}/',
                'password_reset_request': '/api/password-reset/request/',
                'password_reset': '/api/password-reset/{token}/',
            },
            'profile': {
                'get_profile': '/api/profile/',
                'update_profile': '/api/profile/update/',
                'update_profile_picture': '/api/profile/update-picture/',
                'get_user_profile': '/api/users/{username}/profile/',
            },
            'posts': {
                'list_create': '/api/posts/',
                'detail': '/api/posts/{post_id}/',
                'like': '/api/posts/{post_id}/like/',
                'dislike': '/api/posts/{post_id}/dislike/',
                'comment': '/api/posts/{post_id}/comment/',
                'repost': '/api/posts/{post_id}/repost/',
                'thread': '/api/posts/{post_id}/thread/',
                'by_category': '/api/posts/category/{category_id}/',
                'user_posts': '/api/users/{username}/posts/',
                'saved_posts': '/api/posts/saved/',
                'save_post': '/api/posts/{post_id}/save/',
                'unsave_post': '/api/posts/{post_id}/unsave/',
            },
            'social': {
                'follow': '/api/users/{username}/follow/',
                'unfollow': '/api/users/{username}/unfollow/',
                'followers': '/api/users/{username}/followers/',
                'following': '/api/users/{username}/following/',
            },
            'notifications': {
                'list': '/api/notifications/',
                'mark_read': '/api/notifications/mark-read/',
            },
            'messaging': {
                'conversations': '/api/conversations/',
                'conversation_detail': '/api/conversations/{conversation_id}/',
                'send_message': '/api/conversations/{conversation_id}/send/',
                'start_conversation': '/api/conversations/start/{username}/',
            }
        }
    })


# ════════════════════════════════════════════════════════════
# 🔐 Authentication Endpoints
# ════════════════════════════════════════════════════════════

@csrf_exempt
@require_http_methods(["POST"])
def signup(request):
    """Register a new user"""
    try:
        data = json.loads(request.body)
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        password_confirm = data.get('password_confirm', '')

        # Validation
        if not all([username, email, password, password_confirm]):
            return JsonResponse({
                'success': False,
                'message': 'All fields are required'
            }, status=400)

        if password != password_confirm:
            return JsonResponse({
                'success': False,
                'message': 'Passwords do not match'
            }, status=400)

        if len(password) < 8:
            return JsonResponse({
                'success': False,
                'message': 'Password must be at least 8 characters'
            }, status=400)

        if User.objects.filter(username=username).exists():
            return JsonResponse({
                'success': False,
                'message': 'Username already exists'
            }, status=400)

        if User.objects.filter(email=email).exists():
            return JsonResponse({
                'success': False,
                'message': 'Email already exists'
            }, status=400)

        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_active=False
        )

        # Send verification email
        verification_token = user.generate_email_verification_token()
        user.email_verification_sent_at = timezone.now()
        user.save()

        host = request.scheme + '://' + request.get_host()
        verification_link = f"{host}/api/verify-email/{verification_token}/"
        
        try:
            send_mail(
                'Email Verification',
                f'Click this link to verify your email: {verification_link}',
                settings.DEFAULT_FROM_EMAIL or 'noreply@example.com',
                [user.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Email sending failed: {e}")

        return JsonResponse({
            'success': True,
            'message': 'Signup successful. Please check your email to verify your account.',
            'user': serialize_user(user, include_sensitive=True)
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def verify_email(request, token):
    """Verify user email"""
    try:
        user = get_object_or_404(User, email_verification_token=token)
        
        if not user.is_email_verification_token_valid():
            return JsonResponse({
                'success': False,
                'message': 'Verification token has expired'
            }, status=400)
        
        user.verify_email()
        user.is_active = True
        user.save()
        
        # لاگین کردن کاربر بعد از تأیید ایمیل
        login(request, user)
        
        return JsonResponse({
            'success': True,
            'message': 'Email verified successfully. You are now logged in.',
            'user': serialize_user(user, include_sensitive=True)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def login_user(request):
    """User login"""
    try:
        data = json.loads(request.body)
        username_or_email = data.get('username_or_email', '').strip()
        password = data.get('password', '')
        remember = data.get('remember', False)

        if not all([username_or_email, password]):
            return JsonResponse({
                'success': False,
                'message': 'Username/Email and password are required'
            }, status=400)

        # Find user
        user = User.objects.filter(email=username_or_email).first() or \
               User.objects.filter(username=username_or_email).first()

        if user and user.check_password(password):
            if not user.is_active:
                return JsonResponse({
                    'success': False,
                    'message': 'Please verify your email first'
                }, status=400)

            login(request, user)
            
            # Set session expiry
            if remember:
                request.session.set_expiry(60 * 60 * 24 * 30)  # 30 days
            else:
                request.session.set_expiry(0)  # Browser close
            
            return JsonResponse({
                'success': True,
                'message': 'Login successful',
                'user': serialize_user(user, include_sensitive=True)
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Invalid credentials'
            }, status=401)

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def logout_user(request):
    """User logout"""
    logout(request)
    return JsonResponse({
        'success': True,
        'message': 'Logout successful'
    })


@csrf_exempt
@require_http_methods(["POST"])
def request_password_reset(request):
    """Request password reset"""
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip()

        if not email:
            return JsonResponse({
                'success': False,
                'message': 'Email is required'
            }, status=400)

        user = User.objects.filter(email=email).first()

        if user:
            reset_token = user.generate_password_reset_token()
            user.password_reset_sent_at = timezone.now()
            user.save()

            host = request.scheme + '://' + request.get_host()
            reset_link = f"{host}/api/password-reset/{reset_token}/"
            
            try:
                send_mail(
                    'Password Reset Request',
                    f'Click this link to reset your password: {reset_link}',
                    settings.DEFAULT_FROM_EMAIL or 'noreply@example.com',
                    [user.email],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Email sending failed: {e}")

        return JsonResponse({
            'success': True,
            'message': 'If this email exists, a password reset link has been sent'
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def reset_password(request, token):
    """Reset password with token"""
    try:
        user = get_object_or_404(User, password_reset_token=token)

        token_age = timezone.now() - user.password_reset_sent_at
        if token_age > timedelta(hours=1):
            return JsonResponse({
                'success': False,
                'message': 'Password reset token has expired'
            }, status=400)

        data = json.loads(request.body)
        password = data.get('password', '')
        password_confirm = data.get('password_confirm', '')

        if not all([password, password_confirm]):
            return JsonResponse({
                'success': False,
                'message': 'Password and confirmation are required'
            }, status=400)

        if password != password_confirm:
            return JsonResponse({
                'success': False,
                'message': 'Passwords do not match'
            }, status=400)

        if len(password) < 8:
            return JsonResponse({
                'success': False,
                'message': 'Password must be at least 8 characters'
            }, status=400)

        user.set_password(password)
        user.password_reset_token = None
        user.password_reset_sent_at = None
        user.save()

        return JsonResponse({
            'success': True,
            'message': 'Password reset successfully. You can now login.'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


# ════════════════════════════════════════════════════════════
# 👤 Profile Endpoints
# ════════════════════════════════════════════════════════════

@require_http_methods(["GET"])
def get_profile(request):
    """Get current user profile"""
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'User not authenticated'
        }, status=401)

    return JsonResponse({
        'success': True,
        'user': serialize_user(request.user, include_sensitive=True, current_user=request.user)
    })


@require_http_methods(["GET"])
def get_user_profile(request, username):
    """Get any user's public profile"""
    user = get_object_or_404(User, username=username)
    
    # اگر کاربر جاری باشد، اطلاعات حساس شامل شود
    include_sensitive = request.user.is_authenticated and request.user.id == user.id
    
    return JsonResponse({
        'success': True,
        'user': serialize_user(user, include_sensitive=include_sensitive, current_user=request.user)
    })


@csrf_exempt
@require_http_methods(["PUT", "POST", "PATCH"])
def update_profile(request):
    """Update user profile"""
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'User not authenticated'
        }, status=401)

    try:
        data = json.loads(request.body)
        user = request.user

        # Update allowed fields
        allowed_fields = ['first_name', 'last_name', 'student_id', 'bio']
        for field in allowed_fields:
            if field in data:
                setattr(user, field, data[field])

        user.save()

        return JsonResponse({
            'success': True,
            'message': 'Profile updated successfully',
            'user': serialize_user(user, include_sensitive=True, current_user=request.user)
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def update_profile_picture(request):
    """Update profile picture"""
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'User not authenticated'
        }, status=401)

    try:
        if 'profile_picture' not in request.FILES:
            return JsonResponse({
                'success': False,
                'message': 'No image file provided'
            }, status=400)

        profile_picture = request.FILES['profile_picture']
        user = request.user

        # Delete old picture
        if user.profile_picture:
            if user.profile_picture.name:
                user.profile_picture.delete(save=False)

        user.profile_picture = profile_picture
        user.save()

        return JsonResponse({
            'success': True,
            'message': 'Profile picture updated successfully',
            'profile_picture': user.profile_picture.url if user.profile_picture else None
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


# ════════════════════════════════════════════════════════════
# 🤝 Social Endpoints
# ════════════════════════════════════════════════════════════

@csrf_exempt
@require_http_methods(["POST"])
def follow_user(request, username):
    """Follow a user"""
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'Authentication required'
        }, status=401)
    
    user_to_follow = get_object_or_404(User, username=username)
    
    if user_to_follow == request.user:
        return JsonResponse({
            'success': False,
            'message': 'You cannot follow yourself'
        }, status=400)
    
    if request.user.follow(user_to_follow):
        # ایجاد نوتیفیکیشن
        Notification.objects.create(
            recipient=user_to_follow,
            sender=request.user,
            notif_type='follow',
            message=f'{request.user.username} started following you'
        )
        
        return JsonResponse({
            'success': True,
            'message': f'You are now following {username}',
            'followers_count': user_to_follow.followers_count
        })
    else:
        return JsonResponse({
            'success': False,
            'message': f'You are already following {username}'
        }, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def unfollow_user(request, username):
    """Unfollow a user"""
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'Authentication required'
        }, status=401)
    
    user_to_unfollow = get_object_or_404(User, username=username)
    
    if request.user.unfollow(user_to_unfollow):
        return JsonResponse({
            'success': True,
            'message': f'You have unfollowed {username}',
            'followers_count': user_to_unfollow.followers_count
        })
    else:
        return JsonResponse({
            'success': False,
            'message': f'You are not following {username}'
        }, status=400)


@require_http_methods(["GET"])
def user_followers(request, username):
    """Get user's followers"""
    user = get_object_or_404(User, username=username)
    followers = user.followers.all()
    
    return JsonResponse({
        'success': True,
        'followers': [serialize_user(f, current_user=request.user) for f in followers],
        'count': len(followers)
    })


@require_http_methods(["GET"])
def user_following(request, username):
    """Get users that this user is following"""
    user = get_object_or_404(User, username=username)
    following = user.following.all()
    
    return JsonResponse({
        'success': True,
        'following': [serialize_user(f, current_user=request.user) for f in following],
        'count': len(following)
    })


# ════════════════════════════════════════════════════════════
# 📝 Post Endpoints
# ════════════════════════════════════════════════════════════

@csrf_exempt
@require_http_methods(["GET", "POST"])
def posts_list_create(request):
    """List all posts or create new post"""
    
    if request.method == 'GET':
        # پارامترهای جستجو
        category = request.GET.get('category')
        username = request.GET.get('username')
        limit = int(request.GET.get('limit', 20))
        offset = int(request.GET.get('offset', 0))
        
        # ساخت کوئری
        query = Post.objects.filter(parent=None)
        
        if category:
            query = query.filter(category=category)
        
        if username:
            user = get_object_or_404(User, username=username)
            query = query.filter(author=user)
        
        posts = query.select_related('author').prefetch_related(
            'media', 'mentions', 'reactions'
        ).order_by('-created_at')[offset:offset + limit]
        
        return JsonResponse({
            'success': True,
            'posts': [serialize_post(p, include_user_info=True, current_user=request.user) for p in posts],
            'count': len(posts),
            'has_more': len(posts) == limit
        })
    
    # POST - ایجاد پست جدید
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'Authentication required'
        }, status=401)

    try:
        content = request.POST.get('content', '').strip()
        tags = request.POST.get('tags', '').strip()
        mentions_raw = request.POST.get('mentions', '').strip()
        parent_id = request.POST.get('parent')
        category = request.POST.get('category', '').strip()

        if not content and not request.FILES:
            return JsonResponse({
                'success': False,
                'message': 'Post content or media required'
            }, status=400)

        # دسته‌بندی برای پست‌های اصلی الزامی است
        if not parent_id and not category:
            return JsonResponse({
                'success': False,
                'message': 'Room/Category is required'
            }, status=400)

        parent = None
        if parent_id:
            parent = Post.objects.filter(id=parent_id).first()

        post = Post.objects.create(
            author=request.user,
            content=content,
            tags=tags,
            parent=parent,
            category=category
        )

        # مدیریت منشن‌ها
        if mentions_raw:
            usernames = [u.strip() for u in mentions_raw.split(',') if u.strip()]
            mentioned_users = User.objects.filter(username__in=usernames)
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

        # مدیریت فایل‌های مدیا
        for f in request.FILES.getlist('media'):
            ctype = f.content_type or mimetypes.guess_type(f.name)[0] or ''
            if ctype.startswith('image/'):
                mtype = 'image'
            elif ctype.startswith('video/'):
                mtype = 'video'
            elif ctype.startswith('audio/'):
                mtype = 'audio'
            else:
                mtype = 'file'
            PostMedia.objects.create(post=post, file=f, media_type=mtype)

        return JsonResponse({
            'success': True,
            'post': serialize_post(post, include_user_info=True, current_user=request.user)
        }, status=201)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@require_http_methods(["GET"])
def post_detail(request, post_id):
    """Get single post details with comments and replies"""
    post = get_object_or_404(Post, id=post_id)
    data = serialize_post(post, include_user_info=True, current_user=request.user)
    
    # Get comments
    comments = Comment.objects.filter(post=post).select_related('user').order_by('created_at')
    data['comments'] = [serialize_comment(c, current_user=request.user) for c in comments]
    
    # Get replies
    replies = Post.objects.filter(parent=post).select_related('author').prefetch_related(
        'media', 'mentions'
    ).order_by('created_at')
    data['replies'] = [serialize_post(r, include_user_info=True, current_user=request.user) for r in replies]
    
    return JsonResponse({
        'success': True,
        'post': data
    })


@csrf_exempt
@require_http_methods(["POST"])
def post_like(request, post_id):
    """Like/unlike a post"""
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'Authentication required'
        }, status=401)
    
    post = get_object_or_404(Post, id=post_id)
    r = Reaction.objects.filter(user=request.user, post=post).first()
    
    if r and r.reaction == 'like':
        # Unlike
        r.delete()
        likes_count = post.reactions.filter(reaction='like').count()
        return JsonResponse({
            'success': True,
            'message': 'Unliked',
            'likes_count': likes_count,
            'user_reaction': None
        })
    else:
        # Like
        if r:
            r.reaction = 'like'
            r.save()
        else:
            Reaction.objects.create(user=request.user, post=post, reaction='like')
        
        if post.author != request.user:
            Notification.objects.create(
                recipient=post.author,
                sender=request.user,
                notif_type='like',
                post=post,
                message=f'{request.user.username} liked your post'
            )
        
        likes_count = post.reactions.filter(reaction='like').count()
        return JsonResponse({
            'success': True,
            'message': 'Liked',
            'likes_count': likes_count,
            'user_reaction': 'like'
        })


@csrf_exempt
@require_http_methods(["POST"])
def post_dislike(request, post_id):
    """Dislike/remove dislike from a post"""
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'Authentication required'
        }, status=401)
    
    post = get_object_or_404(Post, id=post_id)
    r = Reaction.objects.filter(user=request.user, post=post).first()
    
    if r and r.reaction == 'dislike':
        # Remove dislike
        r.delete()
        dislikes_count = post.reactions.filter(reaction='dislike').count()
        return JsonResponse({
            'success': True,
            'message': 'Removed dislike',
            'dislikes_count': dislikes_count,
            'user_reaction': None
        })
    else:
        # Dislike
        if r:
            r.reaction = 'dislike'
            r.save()
        else:
            Reaction.objects.create(user=request.user, post=post, reaction='dislike')
        
        dislikes_count = post.reactions.filter(reaction='dislike').count()
        return JsonResponse({
            'success': True,
            'message': 'Disliked',
            'dislikes_count': dislikes_count,
            'user_reaction': 'dislike'
        })


@csrf_exempt
@require_http_methods(["POST"])
def post_comment(request, post_id):
    """Add comment to a post"""
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'Authentication required'
        }, status=401)
    
    post = get_object_or_404(Post, id=post_id)
    
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON'
        }, status=400)
    
    content = data.get('content', '').strip()
    parent_id = data.get('parent')
    
    if not content:
        return JsonResponse({
            'success': False,
            'message': 'Comment content required'
        }, status=400)
    
    parent = None
    if parent_id:
        parent = Comment.objects.filter(id=parent_id, post=post).first()
    
    comment = Comment.objects.create(
        user=request.user,
        post=post,
        content=content,
        parent=parent
    )
    
    # ایجاد نوتیفیکیشن
    if post.author != request.user:
        Notification.objects.create(
            recipient=post.author,
            sender=request.user,
            notif_type='comment',
            post=post,
            comment=comment,
            message=f'{request.user.username} commented on your post'
        )
    
    # اگر کامنت پاسخ به کامنت دیگری است
    if parent and parent.user != request.user:
        Notification.objects.create(
            recipient=parent.user,
            sender=request.user,
            notif_type='reply',
            post=post,
            comment=comment,
            message=f'{request.user.username} replied to your comment'
        )
    
    return JsonResponse({
        'success': True,
        'comment': serialize_comment(comment, current_user=request.user),
        'comments_count': post.comments.count()
    })


@csrf_exempt
@require_http_methods(["POST"])
def post_repost(request, post_id):
    """Repost a post"""
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'Authentication required'
        }, status=401)
    
    post = get_object_or_404(Post, id=post_id)
    
    new_post = Post.objects.create(
        author=request.user,
        content=post.content,
        is_repost=True,
        original_post=post,
        tags=post.tags,
        category=post.category
    )
    
    for mu in post.mentions.all():
        new_post.mentions.add(mu)
    
    for m in post.media.all():
        PostMedia.objects.create(post=new_post, file=m.file, media_type=m.media_type)
    
    if post.author != request.user:
        Notification.objects.create(
            recipient=post.author,
            sender=request.user,
            notif_type='repost',
            post=post,
            message=f'{request.user.username} reposted your post'
        )
    
    return JsonResponse({
        'success': True,
        'post': serialize_post(new_post, include_user_info=True, current_user=request.user)
    })


@require_http_methods(["GET"])
def posts_by_category(request, category_id):
    """Get posts by category/room"""
    posts = Post.objects.filter(
        category=category_id,
        parent=None
    ).select_related('author').prefetch_related(
        'media', 'mentions'
    ).order_by('-created_at')[:100]
    
    return JsonResponse({
        'success': True,
        'posts': [serialize_post(p, include_user_info=True, current_user=request.user) for p in posts],
        'category': category_id,
        'count': len(posts)
    })


@require_http_methods(["GET"])
def user_posts(request, username):
    """Get posts by specific user"""
    user = get_object_or_404(User, username=username)
    posts = Post.objects.filter(
        author=user,
        parent=None
    ).select_related('author').prefetch_related(
        'media', 'mentions'
    ).order_by('-created_at')[:100]
    
    return JsonResponse({
        'success': True,
        'posts': [serialize_post(p, include_user_info=True, current_user=request.user) for p in posts],
        'username': username,
        'user': serialize_user(user, include_sensitive=False, current_user=request.user),
        'count': len(posts)
    })


@require_http_methods(["GET"])
def post_thread(request, post_id):
    """Get post thread (post with all its replies)"""
    post = get_object_or_404(Post, id=post_id)
    data = serialize_post(post, include_user_info=True, current_user=request.user)
    
    replies = [
        serialize_post(r, include_user_info=True, current_user=request.user)
        for r in post.replies.select_related('author').prefetch_related(
            'media', 'mentions'
        ).order_by('created_at')
    ]
    data['replies'] = replies
    
    return JsonResponse({
        'success': True,
        'thread': data
    })


@csrf_exempt
@require_http_methods(["POST"])
def save_post(request, post_id):
    """Save a post"""
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'Authentication required'
        }, status=401)
    
    post = get_object_or_404(Post, id=post_id)
    
    if post.saved_by.filter(id=request.user.id).exists():
        return JsonResponse({
            'success': False,
            'message': 'Post already saved'
        }, status=400)
    
    post.saved_by.add(request.user)
    
    return JsonResponse({
        'success': True,
        'message': 'Post saved successfully'
    })


@csrf_exempt
@require_http_methods(["POST"])
def unsave_post(request, post_id):
    """Unsave a post"""
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'Authentication required'
        }, status=401)
    
    post = get_object_or_404(Post, id=post_id)
    
    if not post.saved_by.filter(id=request.user.id).exists():
        return JsonResponse({
            'success': False,
            'message': 'Post not saved'
        }, status=400)
    
    post.saved_by.remove(request.user)
    
    return JsonResponse({
        'success': True,
        'message': 'Post unsaved successfully'
    })


@require_http_methods(["GET"])
def saved_posts(request):
    """Get user's saved posts"""
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'Authentication required'
        }, status=401)
    
    saved_posts = request.user.saved_posts.filter(parent=None)
    
    return JsonResponse({
        'success': True,
        'posts': [serialize_post(p, include_user_info=True, current_user=request.user) for p in saved_posts],
        'count': len(saved_posts)
    })


@csrf_exempt
@require_http_methods(["POST"])
def like_comment(request, comment_id):
    """Like/unlike a comment"""
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'Authentication required'
        }, status=401)
    
    comment = get_object_or_404(Comment, id=comment_id)
    
    if comment.likes.filter(id=request.user.id).exists():
        comment.likes.remove(request.user)
        action = 'unliked'
    else:
        comment.likes.add(request.user)
        action = 'liked'
    
    return JsonResponse({
        'success': True,
        'message': f'Comment {action}',
        'likes_count': comment.likes_count,
        'is_liked': comment.likes.filter(id=request.user.id).exists()
    })


# ════════════════════════════════════════════════════════════
# 🔔 Notification Endpoints
# ════════════════════════════════════════════════════════════

@require_http_methods(["GET"])
def notifications_list(request):
    """Get user notifications"""
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'Authentication required'
        }, status=401)
    
    notifs = Notification.objects.filter(
        recipient=request.user
    ).select_related('sender', 'post', 'comment').order_by('-created_at')[:100]
    
    return JsonResponse({
        'success': True,
        'notifications': [serialize_notification(n) for n in notifs],
        'unread_count': notifs.filter(is_read=False).count()
    })


@csrf_exempt
@require_http_methods(["POST"])
def notifications_mark_read(request):
    """Mark notifications as read"""
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'Authentication required'
        }, status=401)
    
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON'
        }, status=400)
    
    ids = data.get('ids', [])
    
    if not ids:
        # Mark all as read
        Notification.objects.filter(recipient=request.user).update(is_read=True)
    else:
        # Mark specific notifications as read
        Notification.objects.filter(
            recipient=request.user,
            id__in=ids
        ).update(is_read=True)
    
    return JsonResponse({
        'success': True,
        'message': 'Notifications marked as read'
    })


# ════════════════════════════════════════════════════════════
# 💬 Messaging Endpoints
# ════════════════════════════════════════════════════════════

@require_http_methods(["GET"])
def conversations_list(request):
    """Get user's conversations"""
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'Authentication required'
        }, status=401)
    
    conversations = Conversation.objects.filter(participants=request.user)
    
    return JsonResponse({
        'success': True,
        'conversations': [serialize_conversation(c, request.user) for c in conversations],
        'count': len(conversations)
    })


@csrf_exempt
@require_http_methods(["POST"])
def start_conversation(request, username):
    """Start a new conversation"""
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'Authentication required'
        }, status=401)
    
    other_user = get_object_or_404(User, username=username)
    
    if other_user == request.user:
        return JsonResponse({
            'success': False,
            'message': 'Cannot start conversation with yourself'
        }, status=400)
    
    # بررسی وجود مکالمه قبلی
    conversation = Conversation.objects.filter(participants=request.user).filter(participants=other_user).first()
    
    if not conversation:
        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, other_user)
    
    return JsonResponse({
        'success': True,
        'conversation_id': conversation.id,
        'message': 'Conversation started successfully'
    })


@require_http_methods(["GET"])
def conversation_detail(request, conversation_id):
    """Get conversation messages"""
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'Authentication required'
        }, status=401)
    
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    
    # علامت‌گذاری پیام‌ها به عنوان خوانده شده
    conversation.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
    
    messages = conversation.messages.all()
    
    return JsonResponse({
        'success': True,
        'conversation': serialize_conversation(conversation, request.user),
        'messages': [serialize_message(m) for m in messages],
        'count': len(messages)
    })


@csrf_exempt
@require_http_methods(["POST"])
def send_message(request, conversation_id):
    """Send a message in conversation"""
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'Authentication required'
        }, status=401)
    
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    
    try:
        data = request.POST
        content = data.get('content', '').strip()
        image = request.FILES.get('image')
        file = request.FILES.get('file')
        
        if not content and not image and not file:
            return JsonResponse({
                'success': False,
                'message': 'Message content or file is required'
            }, status=400)
        
        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=content,
            image=image,
            file=file
        )
        
        # آپدیت زمان مکالمه
        conversation.updated_at = timezone.now()
        conversation.save()
        
        return JsonResponse({
            'success': True,
            'message': serialize_message(message)
        }, status=201)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)