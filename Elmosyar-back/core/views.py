from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
import json
from datetime import timedelta
import mimetypes

from .models import User, Post, PostMedia, Comment, Notification, Reaction

# Utility Functions
def serialize_user(user):
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'student_id': user.student_id,
        'bio': user.bio,
        'profile_picture': user.profile_picture.url if user.profile_picture else None,
        'is_email_verified': user.is_email_verified,
        'created_at': user.created_at.isoformat(),
    }

def serialize_post(post):
    media_list = []
    for m in post.media.all():
        media_list.append({
            'id': m.id,
            'url': m.file.url if m.file else '',
            'type': m.media_type,
        })
    
    return {
        'id': post.id,
        'author': {
            'username': post.author.username,
            'profile_picture': post.author.profile_picture.url if post.author.profile_picture else None,
        },
        'content': post.content,
        'created_at': post.created_at.isoformat(),
        'tags': [t.strip() for t in post.tags.split(',')] if post.tags else [],
        'mentions': [u.username for u in post.mentions.all()],
        'media': media_list,
        'likes_count': post.reactions.filter(reaction='like').count(),
        'dislikes_count': post.reactions.filter(reaction='dislike').count(),
        'comments_count': post.comments.count(),
        'reposts_count': post.reposts.count(),
        'replies_count': post.replies.count(),
        'is_repost': post.is_repost,
        'original_post_id': post.original_post.id if post.original_post else None,
        'parent_id': post.parent.id if post.parent else None,
        'category': post.category,
    }

def serialize_comment(comment):
    return {
        'id': comment.id,
        'user': {
            'username': comment.user.username,
            'profile_picture': comment.user.profile_picture.url if comment.user.profile_picture else None,
        },
        'content': comment.content,
        'created_at': comment.created_at.isoformat(),
        'parent_id': comment.parent.id if comment.parent else None,
        'replies_count': comment.replies.count(),
    }

# Authentication APIs
@csrf_exempt
@require_http_methods(["POST"])
def signup(request):
    try:
        data = json.loads(request.body)
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        password_confirm = data.get('password_confirm', '')

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

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_active=False
        )

        verification_token = user.generate_email_verification_token()
        user.email_verification_sent_at = timezone.now()
        user.save()

        host = request.scheme + '://' + request.get_host()
        verification_link = f"{host}/api/verify-email/{verification_token}/"
        send_mail(
            'Email Verification',
            f'Click this link to verify your email: {verification_link}',
            settings.DEFAULT_FROM_EMAIL or 'noreply@example.com',
            [user.email],
            fail_silently=False,
        )

        return JsonResponse({
            'success': True,
            'message': 'Signup successful. Please check your email to verify your account.',
            'user_id': user.id
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
@require_http_methods(["POST"])
def login_user(request):
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

        user = User.objects.filter(
            email=username_or_email
        ).first() or User.objects.filter(
            username=username_or_email
        ).first()

        if user and user.check_password(password):
            if not user.is_active:
                return JsonResponse({
                    'success': False,
                    'message': 'Please verify your email first'
                }, status=400)

            login(request, user)
            if remember:
                request.session.set_expiry(60 * 60 * 24 * 30)
            else:
                request.session.set_expiry(0)

            return JsonResponse({
                'success': True,
                'message': 'Login successful',
                'user': serialize_user(user)
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
    logout(request)
    return JsonResponse({
        'success': True,
        'message': 'Logout successful'
    })

@csrf_exempt
@require_http_methods(["GET"])
def verify_email(request, token):
    try:
        user = get_object_or_404(User, email_verification_token=token)

        token_age = timezone.now() - user.email_verification_sent_at
        if token_age > timedelta(hours=24):
            return JsonResponse({
                'success': False,
                'message': 'Verification token has expired'
            }, status=400)

        user.verify_email()
        user.is_active = True
        user.save()

        return JsonResponse({
            'success': True,
            'message': 'Email verified successfully. You can now login.'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

# Profile APIs
@require_http_methods(["GET"])
def get_profile(request):
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'User not authenticated'
        }, status=401)

    return JsonResponse({
        'success': True,
        'user': serialize_user(request.user)
    })

@csrf_exempt
@require_http_methods(["POST"])
def update_profile(request):
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'User not authenticated'
        }, status=401)

    try:
        data = json.loads(request.body)
        user = request.user

        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'student_id' in data:
            user.student_id = data['student_id']
        if 'bio' in data:
            user.bio = data['bio']

        user.save()

        return JsonResponse({
            'success': True,
            'message': 'Profile updated successfully',
            'user': serialize_user(user)
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

        if user.profile_picture:
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

# Post APIs
@csrf_exempt
@require_http_methods(["GET", "POST"])
def posts_list_create(request):
    if request.method == 'GET':
        posts = Post.objects.select_related('author').prefetch_related('media', 'mentions').order_by('-created_at')[:100]
        return JsonResponse({
            'success': True, 
            'posts': [serialize_post(p) for p in posts]
        })

    # POST - Create new post
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False, 
            'message': 'Authentication required'
        }, status=401)

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

    # Handle mentions
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
                    message=f'{request.user.username} mentioned you'
                )

    # Handle media files
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
        'post': serialize_post(post)
    }, status=201)

@require_http_methods(["GET"])
def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    return JsonResponse({
        'success': True, 
        'post': serialize_post(post)
    })

@require_http_methods(["GET"])
def post_thread(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    data = serialize_post(post)
    replies = [serialize_post(r) for r in post.replies.select_related('author').prefetch_related('media','mentions').order_by('created_at')]
    data['replies'] = replies
    return JsonResponse({
        'success': True, 
        'thread': data
    })

@require_http_methods(["GET"])
def posts_by_category(request, category_id):
    posts = Post.objects.filter(category=category_id).select_related('author').prefetch_related('media', 'mentions').order_by('-created_at')[:100]
    return JsonResponse({
        'success': True, 
        'posts': [serialize_post(p) for p in posts]
    })

@require_http_methods(["GET"])
def user_posts(request, username):
    user = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=user).select_related('author').prefetch_related('media', 'mentions').order_by('-created_at')[:100]
    
    return JsonResponse({
        'success': True, 
        'posts': [serialize_post(p) for p in posts],
        'user': serialize_user(user)
    })

# Post Interaction APIs
@csrf_exempt
@require_http_methods(["POST"])
def post_like(request, post_id):
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False, 
            'message': 'Authentication required'
        }, status=401)
    
    post = get_object_or_404(Post, id=post_id)
    r = Reaction.objects.filter(user=request.user, post=post).first()
    
    if r and r.reaction == 'like':
        r.delete()
        likes_count = post.reactions.filter(reaction='like').count()
        return JsonResponse({
            'success': True, 
            'message': 'Unliked', 
            'likes_count': likes_count
        })
    else:
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
        
        return JsonResponse({
            'success': True, 
            'message': 'Liked', 
            'likes_count': post.reactions.filter(reaction='like').count()
        })

@csrf_exempt
@require_http_methods(["POST"])
def post_dislike(request, post_id):
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False, 
            'message': 'Authentication required'
        }, status=401)
    
    post = get_object_or_404(Post, id=post_id)
    r = Reaction.objects.filter(user=request.user, post=post).first()
    
    if r and r.reaction == 'dislike':
        r.delete()
        dislikes_count = post.reactions.filter(reaction='dislike').count()
        return JsonResponse({
            'success': True, 
            'message': 'Removed dislike', 
            'dislikes_count': dislikes_count
        })
    else:
        if r:
            r.reaction = 'dislike'
            r.save()
        else:
            Reaction.objects.create(user=request.user, post=post, reaction='dislike')
        
        return JsonResponse({
            'success': True, 
            'message': 'Disliked', 
            'dislikes_count': post.reactions.filter(reaction='dislike').count()
        })

@csrf_exempt
@require_http_methods(["POST"])
def post_comment(request, post_id):
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
    
    if post.author != request.user:
        Notification.objects.create(
            recipient=post.author, 
            sender=request.user, 
            notif_type='comment', 
            post=post, 
            comment=comment,
            message=f'{request.user.username} commented on your post'
        )
    
    return JsonResponse({
        'success': True, 
        'comment_id': comment.id, 
        'comments_count': post.comments.count()
    })

@csrf_exempt
@require_http_methods(["POST"])
def post_repost(request, post_id):
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
        tags=post.tags
    )
    
    # Copy mentions
    for mu in post.mentions.all():
        new_post.mentions.add(mu)
    
    # Copy media references
    for m in post.media.all():
        PostMedia.objects.create(post=new_post, file=m.file, media_type=m.media_type)
    
    # Notify original author
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
        'post': serialize_post(new_post)
    })

# Comment APIs
@require_http_methods(["GET"])
def post_comments(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = Comment.objects.filter(post=post, parent=None).select_related('user').prefetch_related('replies')
    
    def serialize_comment_with_replies(comment):
        data = serialize_comment(comment)
        data['replies'] = [serialize_comment_with_replies(reply) for reply in comment.replies.all()]
        return data
    
    comments_data = [serialize_comment_with_replies(comment) for comment in comments]
    
    return JsonResponse({
        'success': True, 
        'comments': comments_data
    })

# Notification APIs
@require_http_methods(["GET"])
def notifications_list(request):
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False, 
            'message': 'Authentication required'
        }, status=401)
    
    notifs = Notification.objects.filter(recipient=request.user).select_related('sender', 'post', 'comment').order_by('-created_at')[:100]
    data = []
    for n in notifs:
        data.append({
            'id': n.id,
            'sender': serialize_user(n.sender),
            'type': n.notif_type,
            'post': serialize_post(n.post) if n.post else None,
            'comment': serialize_comment(n.comment) if n.comment else None,
            'message': n.message,
            'is_read': n.is_read,
            'created_at': n.created_at.isoformat(),
        })
    
    return JsonResponse({
        'success': True, 
        'notifications': data
    })

@csrf_exempt
@require_http_methods(["POST"])
def notifications_mark_read(request):
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
    Notification.objects.filter(recipient=request.user, id__in=ids).update(is_read=True)
    
    return JsonResponse({'success': True})

# Password Reset APIs
@csrf_exempt
@require_http_methods(["POST"])
def request_password_reset(request):
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
            reset_link = f"{host}/reset-password/?token={reset_token}"
            send_mail(
                'Password Reset Request',
                f'Click this link to reset your password: {reset_link}',
                settings.DEFAULT_FROM_EMAIL or 'noreply@example.com',
                [user.email],
                fail_silently=False,
            )

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