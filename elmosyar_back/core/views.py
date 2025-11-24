import logging
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import authenticate
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError
from datetime import timedelta
from django.db import transaction
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from django.db.models import Q, Count, F
from django.core.paginator import Paginator
import json
import mimetypes
import os

from .models import User, Post, PostMedia, Comment, Notification, Reaction, Conversation, Message, UserFollow
from .serializers import (
    UserSerializer, SignUpSerializer, LoginSerializer, PostSerializer, 
    CommentSerializer, NotificationSerializer, ConversationSerializer, 
    MessageSerializer, PostMediaSerializer, ResendVerificationSerializer
)

# Constants
MAX_PROFILE_PICTURE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_MEDIA_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_POST_CONTENT_LENGTH = 5000
MAX_COMMENT_CONTENT_LENGTH = 1000
MAX_MESSAGE_CONTENT_LENGTH = 2000

logging.basicConfig(
    filename='./server.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# ════════════════════════════════════════════════════════════
# Tokens
# ════════════════════════════════════════════════════════════

class VerifyTokenView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        token = request.data.get('token') or request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not token:
            return Response({
                'success': False,
                'message': 'Token is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            AccessToken(token)
            return Response({
                'success': True,
                'message': 'Token is valid'
            }, status=status.HTTP_200_OK)
        except TokenError as e:
            logger.warning(f"Token validation failed: {str(e)}")
            return Response({
                'success': False,
                'message': 'Token is invalid or expired'
            }, status=status.HTTP_400_BAD_REQUEST)

class RefreshTokenView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({
                'success': False,
                'message': 'Refresh token is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            refresh = RefreshToken(refresh_token)
            return Response({
                'success': True,
                'access': str(refresh.access_token)
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Token refresh failed: {str(e)}")
            return Response({
                'success': False,
                'message': 'Invalid refresh token'
            }, status=status.HTTP_400_BAD_REQUEST)

# ════════════════════════════════════════════════════════════
# 🏠 Basic Endpoint
# ════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([AllowAny])
def index(request):
    """API root endpoint"""
    return Response({
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


def send_verification_email(user):
    """Helper function to send verification email"""
    verification_token = user.generate_email_verification_token()
    verification_link = f"{settings.FRONTEND_URL}/verify-email/{verification_token}/"
    
    try:
        send_mail(
            'Email Verification',
            f'Click this link to verify your email: {verification_link}',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"Email sending failed: {str(e)}")
        return False


@api_view(['POST'])
@permission_classes([AllowAny])
def resend_verification_email(request):
    """Resend email verification link"""
    serializer = ResendVerificationSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            'success': False,
            'message': 'Validation failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    email = serializer.validated_data['email']
    
    try:
        user = User.objects.get(email=email)
        
        if user.is_email_verified:
            return Response({
                'success': False,
                'message': 'Email is already verified.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        email_sent = send_verification_email(user)
        
        if email_sent:
            return Response({
                'success': True,
                'message': 'Verification email sent successfully. Please check your email.'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': 'Failed to send verification email. Please try again later.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'User with this email does not exist.'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([AllowAny])
def verify_email(request, token):
    """Verify user email"""
    try:
        with transaction.atomic():
            user = get_object_or_404(User, email_verification_token=token)
            
            if user.is_email_verified:
                return Response({
                    'success': False,
                    'message': 'Email is already verified'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not user.is_email_verification_token_valid():
                return Response({
                    'success': False,
                    'message': 'Verification token has expired'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user.verify_email()
            user.is_active = True
            user.save()
            
            # Generate tokens for auto-login
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'success': True,
                'message': 'Email verified successfully',
                'user': UserSerializer(user, context={'request': request}).data,
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh)
                }
            }, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Email verification failed: {str(e)}")
        return Response({
            'success': False,
            'message': 'Verification failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    """Register a new user"""
    serializer = SignUpSerializer(data=request.data)
    if serializer.is_valid():
        with transaction.atomic():
            user = serializer.save()
            
            # Send verification email using helper function
            email_sent = send_verification_email(user)
            
            if email_sent:
                message = 'Signup successful. Please check your email to verify your account.'
            else:
                message = 'Signup successful, but verification email failed to send. Please contact support.'

            return Response({
                'success': True,
                'message': message,
                'user': UserSerializer(user, context={'request': request}).data
            }, status=status.HTTP_201_CREATED)
    
    return Response({
        'success': False,
        'message': 'Validation failed',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Validation failed',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        username_or_email = serializer.validated_data['username_or_email']
        password = serializer.validated_data['password']
        remember_me = serializer.validated_data.get('rememberMe', False)
        
        # Find user by username or email
        user = User.objects.filter(
            Q(email=username_or_email) | Q(username=username_or_email)
        ).first()

        if user and user.check_password(password):
            if not user.is_active:
                return Response({
                    'success': False,
                    'message': 'Account is not active'
                }, status=status.HTTP_400_BAD_REQUEST)

            if not user.is_email_verified:
                return Response({
                    'success': False,
                    'message': 'Please verify your email first'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            if remember_me:
                refresh.set_exp(lifetime=timedelta(days=7))
            
            return Response({
                'success': True,
                'message': 'Login successful',
                'user': UserSerializer(user, context={'request': request}).data,
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh)
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({
                'success': False,
                'message': 'Refresh token is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({
                'success': True,
                'message': 'Logout successful'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Logout failed: {str(e)}")
            return Response({
                'success': False,
                'message': 'Invalid token'
            }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def request_password_reset(request):
    """Request password reset"""
    email = request.data.get('email', '').strip()

    if not email:
        return Response({
            'success': False,
            'message': 'Email is required'
        }, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.filter(email=email).first()

    if user:
        reset_token = user.generate_password_reset_token()
        reset_link = f"{settings.FRONTEND_URL}/password-reset/{reset_token}/"
        
        try:
            send_mail(
                'Password Reset Request',
                f'Click this link to reset your password: {reset_link}',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
        except Exception as e:
            logger.error(f"Password reset email failed: {str(e)}")

    # Always return same message for security
    return Response({
        'success': True,
        'message': 'If this email exists in our system, a password reset link has been sent'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request, token):
    """Reset password with token"""
    try:
        with transaction.atomic():
            user = get_object_or_404(User, password_reset_token=token)

            if not user.is_password_reset_token_valid():
                return Response({
                    'success': False,
                    'message': 'Password reset token has expired'
                }, status=status.HTTP_400_BAD_REQUEST)

            password = request.data.get('password', '')
            password_confirm = request.data.get('password_confirm', '')

            if not all([password, password_confirm]):
                return Response({
                    'success': False,
                    'message': 'Password and confirmation are required'
                }, status=status.HTTP_400_BAD_REQUEST)

            if password != password_confirm:
                return Response({
                    'success': False,
                    'message': 'Passwords do not match'
                }, status=status.HTTP_400_BAD_REQUEST)

            if len(password) < 8:
                return Response({
                    'success': False,
                    'message': 'Password must be at least 8 characters'
                }, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(password)
            user.password_reset_token = None
            user.password_reset_sent_at = None
            user.save()

            return Response({
                'success': True,
                'message': 'Password reset successfully. You can now login.'
            }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Password reset failed: {str(e)}")
        return Response({
            'success': False,
            'message': 'Password reset failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ════════════════════════════════════════════════════════════
# 👤 Profile Endpoints
# ════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_profile(request):
    """Get current user profile"""
    serializer = UserSerializer(request.user, context={'request': request})
    return Response({
        'success': True,
        'user': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_user_profile(request, username):
    """Get any user's public profile"""
    user = get_object_or_404(User, username=username)
    
    # Include sensitive info only for own profile
    include_sensitive = request.user.is_authenticated and request.user.id == user.id
    
    serializer = UserSerializer(user, context={'request': request})
    data = serializer.data
    
    if not include_sensitive:
        data.pop('email', None)
    
    return Response({
        'success': True,
        'user': data
    }, status=status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """Update user profile"""
    user = request.user
    serializer = UserSerializer(user, data=request.data, partial=True, context={'request': request})
    
    if serializer.is_valid():
        with transaction.atomic():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Profile updated successfully',
                'user': serializer.data
            }, status=status.HTTP_200_OK)
    
    return Response({
        'success': False,
        'message': 'Validation failed',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_profile_picture(request):
    """Update profile picture"""
    if 'profile_picture' not in request.FILES:
        return Response({
            'success': False,
            'message': 'No image file provided'
        }, status=status.HTTP_400_BAD_REQUEST)

    profile_picture = request.FILES['profile_picture']
    user = request.user

    # Validate file type
    if not profile_picture.content_type.startswith('image/'):
        return Response({
            'success': False,
            'message': 'Only image files are allowed'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Validate file size
    if profile_picture.size > MAX_PROFILE_PICTURE_SIZE:
        return Response({
            'success': False,
            'message': f'Image file is too large (max {MAX_PROFILE_PICTURE_SIZE // (1024*1024)}MB)'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        with transaction.atomic():
            old_picture_path = user.profile_picture.path if user.profile_picture else None
            
            user.profile_picture = profile_picture
            user.save()
            
            # Delete old picture file
            if old_picture_path and os.path.isfile(old_picture_path):
                os.remove(old_picture_path)
            
            return Response({
                'success': True,
                'message': 'Profile picture updated successfully',
                'profile_picture': user.profile_picture.url
            }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Profile picture update failed: {str(e)}")
        return Response({
            'success': False,
            'message': 'Failed to update profile picture'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_profile_picture(request):
    """Delete profile picture"""
    user = request.user

    if not user.profile_picture:
        return Response({
            'success': False,
            'message': 'No profile picture to delete'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        with transaction.atomic():
            user.profile_picture.delete(save=False)
            user.profile_picture = None
            user.save()

            return Response({
                'success': True,
                'message': 'Profile picture deleted successfully'
            }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Profile picture deletion failed: {str(e)}")
        return Response({
            'success': False,
            'message': 'Failed to delete profile picture'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ════════════════════════════════════════════════════════════
# 🤝 Social Endpoints
# ════════════════════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def follow_user(request, username):
    """Follow a user"""
    try:
        with transaction.atomic():
            user_to_follow = get_object_or_404(User, username=username)
            
            if user_to_follow == request.user:
                return Response({
                    'success': False,
                    'message': 'You cannot follow yourself'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if request.user.following.filter(id=user_to_follow.id).exists():
                return Response({
                    'success': False,
                    'message': f'You are already following {username}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create follow relationship
            UserFollow.objects.create(follower=request.user, following=user_to_follow)
            
            # Update counts using F() to prevent race condition
            User.objects.filter(id=request.user.id).update(
                following_count=F('following_count') + 1
            )
            User.objects.filter(id=user_to_follow.id).update(
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
            
            return Response({
                'success': True,
                'message': f'You are now following {username}',
                'followers_count': user_to_follow.followers_count
            }, status=status.HTTP_200_OK)
            
    except Exception as e:
        logger.error(f"Follow operation failed: {str(e)}")
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
            user_to_unfollow = get_object_or_404(User, username=username)
            
            follow_relation = UserFollow.objects.filter(
                follower=request.user, 
                following=user_to_unfollow
            ).first()
            
            if not follow_relation:
                return Response({
                    'success': False,
                    'message': f'You are not following {username}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            follow_relation.delete()
            
            # Update counts using F() to prevent race condition
            User.objects.filter(id=request.user.id).update(
                following_count=F('following_count') - 1
            )
            User.objects.filter(id=user_to_unfollow.id).update(
                followers_count=F('followers_count') - 1
            )
            
            # Refresh user to get updated counts
            user_to_unfollow.refresh_from_db()
            
            return Response({
                'success': True,
                'message': f'You have unfollowed {username}',
                'followers_count': user_to_unfollow.followers_count
            }, status=status.HTTP_200_OK)
            
    except Exception as e:
        logger.error(f"Unfollow operation failed: {str(e)}")
        return Response({
            'success': False,
            'message': 'Unfollow operation failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def user_followers(request, username):
    """Get user's followers with pagination"""
    user = get_object_or_404(User, username=username)
    
    page = int(request.GET.get('page', 1))
    per_page = min(int(request.GET.get('per_page', 50)), 100)
    
    followers = user.followers.select_related('follower')
    paginator = Paginator(followers, per_page)
    
    try:
        followers_page = paginator.page(page)
    except:
        followers_page = paginator.page(1)
    
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
    user = get_object_or_404(User, username=username)
    
    page = int(request.GET.get('page', 1))
    per_page = min(int(request.GET.get('per_page', 50)), 100)
    
    following = user.following.select_related('following')
    paginator = Paginator(following, per_page)
    
    try:
        following_page = paginator.page(page)
    except:
        following_page = paginator.page(1)
    
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
            user = get_object_or_404(User, username=username)
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
@permission_classes([AllowAny])
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


def _handle_post_reaction(request, post_id, reaction_type):
    """Helper function to handle post reactions"""
    try:
        with transaction.atomic():
            post = get_object_or_404(Post, id=post_id)
            
            if post.author == request.user:
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
        logger.error(f"Reaction handling failed: {str(e)}")
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
                return Response({
                    'success': False,
                    'message': 'Comment content required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if len(content) > MAX_COMMENT_CONTENT_LENGTH:
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
            
            serializer = CommentSerializer(comment, context={'request': request})
            
            return Response({
                'success': True,
                'comment': serializer.data,
                'comments_count': post.comments.count()
            }, status=status.HTTP_201_CREATED)
    except Exception as e:
        logger.error(f"Comment creation failed: {str(e)}")
        return Response({
            'success': False,
            'message': 'Failed to create comment'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
    user = get_object_or_404(User, username=username)
    
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
# 💬 Comment Endpoints
# ════════════════════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def like_comment(request, comment_id):
    """Like/unlike a comment"""
    try:
        with transaction.atomic():
            comment = get_object_or_404(Comment, id=comment_id)
            
            if comment.user == request.user:
                return Response({
                    'success': False,
                    'message': 'You cannot like your own comment'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if comment.likes.filter(id=request.user.id).exists():
                comment.likes.remove(request.user)
                action = 'unliked'
            else:
                comment.likes.add(request.user)
                action = 'liked'
                
                # Create notification
                if comment.user != request.user:
                    Notification.objects.create(
                        recipient=comment.user,
                        sender=request.user,
                        notif_type='like_comment',
                        comment=comment,
                        message=f'{request.user.username} liked your comment'
                    )
            
            return Response({
                'success': True,
                'message': f'Comment {action}',
                'likes_count': comment.likes.count(),
                'is_liked': comment.likes.filter(id=request.user.id).exists()
            }, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Comment like failed: {str(e)}")
        return Response({
            'success': False,
            'message': 'Failed to like comment'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_comment(request, comment_id):
    """Delete a comment"""
    try:
        with transaction.atomic():
            comment = get_object_or_404(Comment, id=comment_id)
            
            if comment.user != request.user:
                return Response({
                    'success': False,
                    'message': 'You can only delete your own comments'
                }, status=status.HTTP_403_FORBIDDEN)
            
            comment.delete()
            return Response({
                'success': True,
                'message': 'Comment deleted successfully'
            }, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Comment deletion failed: {str(e)}")
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
                return Response({
                    'success': False,
                    'message': 'You can only edit your own comments'
                }, status=status.HTTP_403_FORBIDDEN)
            
            content = request.data.get('content', '').strip()
            
            if not content:
                return Response({
                    'success': False,
                    'message': 'Comment content is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if len(content) > MAX_COMMENT_CONTENT_LENGTH:
                return Response({
                    'success': False,
                    'message': f'Comment is too long (max {MAX_COMMENT_CONTENT_LENGTH} characters)'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            comment.content = content
            comment.save()
            
            serializer = CommentSerializer(comment, context={'request': request})
            
            return Response({
                'success': True,
                'message': 'Comment updated successfully',
                'comment': serializer.data
            }, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Comment update failed: {str(e)}")
        return Response({
            'success': False,
            'message': 'Failed to update comment'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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