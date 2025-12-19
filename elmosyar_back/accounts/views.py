from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q
from django.contrib.auth.hashers import make_password
from datetime import timedelta
import os

from .models import User
from .serializers import UserSerializer, SignUpSerializer, LoginSerializer, ResendVerificationSerializer

# جایگزین کردن لاگر قدیمی
from log_manager.log_config import log_info, log_error, log_warning, log_security, log_audit

MAX_PROFILE_PICTURE_SIZE = 1024 * 1024

# ════════════════════════════════════════════════════════════
# Tokens
# ════════════════════════════════════════════════════════════

class VerifyTokenView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        token = request.data.get('token') or request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not token:
            log_warning("Token verification attempt without token", request)
            return Response({
                'success': False,
                'message': 'Token is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            AccessToken(token)
            log_info("Token verification successful", request)
            return Response({
                'success': True,
                'message': 'Token is valid'
            }, status=status.HTTP_200_OK)
        except TokenError as e:
            log_warning(f"Token validation failed: {str(e)}", request, {'token_preview': token[:20]})
            return Response({
                'success': False,
                'message': 'Token is invalid or expired'
            }, status=status.HTTP_400_BAD_REQUEST)

class RefreshTokenView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            log_warning("Refresh attempt without token", request)
            return Response({
                'success': False,
                'message': 'Refresh token is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            refresh = RefreshToken(refresh_token)
            log_info("Token refreshed successfully", request)
            return Response({
                'success': True,
                'access': str(refresh.access_token)
            }, status=status.HTTP_200_OK)
        except Exception as e:
            log_error(f"Token refresh failed: {str(e)}", request, {'token_preview': refresh_token[:20]})
            return Response({
                'success': False,
                'message': 'Invalid refresh token'
            }, status=status.HTTP_400_BAD_REQUEST)


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
        log_info(f"Verification email sent to {user.email} | JUST FOR DEV(Verification link): {verification_link}", None, {'user_id': user.id})
        return True
    except Exception as e:
        log_error(f"Email sending failed: {str(e)}", None, {'user_id': user.id, 'email': user.email})
        return False


@api_view(['POST'])
@permission_classes([AllowAny])
def resend_verification_email(request):
    """Resend email verification link"""
    serializer = ResendVerificationSerializer(data=request.data)
    
    if not serializer.is_valid():
        log_warning(f"Resend verification validation failed", request, {'errors': serializer.errors})
        return Response({
            'success': False,
            'message': 'Validation failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    email = serializer.validated_data['email']
    
    try:
        user = User.objects.get(email=email)
        
        if user.is_email_verified:
            log_warning(f"Attempt to resend verification for already verified email: {email}", request)
            return Response({
                'success': False,
                'message': 'Email is already verified.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        email_sent = send_verification_email(user)
        
        if email_sent:
            log_info(f"Verification email resent to {email}", request, {'user_id': user.id})
            return Response({
                'success': True,
                'message': 'Verification email sent successfully. Please check your email.'
            }, status=status.HTTP_200_OK)
        else:
            log_error(f"Failed to resend verification email to {email}", request, {'user_id': user.id})
            return Response({
                'success': False,
                'message': 'Failed to send verification email. Please try again later.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except User.DoesNotExist:
        log_warning(f"Resend verification for non-existent email: {email}", request)
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
                log_info(f"Email already verified for user {user.username}", request)
                return Response({
                    'success': False,
                    'message': 'Email is already verified'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not user.is_email_verification_token_valid():
                log_warning(f"Expired verification token for user {user.username}", request)
                return Response({
                    'success': False,
                    'message': 'Verification token has expired'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user.verify_email()
            user.is_active = True
            user.save()
            
            log_audit(f"User email verified successfully", request, {
                'user_id': user.id,
                'username': user.username,
                'email': user.email
            })
            
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
        log_error(f"Email verification failed: {str(e)}", request, {'token': token[:20]})
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
            
            # لاگ کردن ثبت‌نام
            log_audit(f"New user registered", request, {
                'user_id': user.id,
                'username': user.username,
                'email': user.email
            })
            
            # Send verification email using helper function
            email_sent = send_verification_email(user)
            
            if email_sent:
                message = 'Signup successful. Please check your email to verify your account.'
                log_info(f"Verification email sent to new user {user.username}", request)
            else:
                message = 'Signup successful, but verification email failed to send. Please contact support.'
                log_error(f"Failed to send verification email to new user {user.username}", request)

            return Response({
                'success': True,
                'message': message,
                'user': UserSerializer(user, context={'request': request}).data
            }, status=status.HTTP_201_CREATED)
    
    log_warning(f"Signup validation failed", request, {'errors': serializer.errors})
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
            log_warning(f"Login validation failed", request, {'errors': serializer.errors})
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
            if not user.is_email_verified:
                log_warning(f"Login attempt with unverified email: {username_or_email}", request)
                if not user.is_email_verification_token_valid():
                    send_verification_email(user)
                    return Response({
                        'success': False,
                        'message': f'Please verify your email ({user.email}) first, new verification email sent'
                    }, status=status.HTTP_400_BAD_REQUEST)
                return Response({
                    'success': False,
                    'message': f'Please verify your email ({user.email}) first'
                }, status=status.HTTP_400_BAD_REQUEST)

            if not user.is_active:
                log_warning(f"Login attempt to inactive account: {username_or_email}", request)
                return Response({
                    'success': False,
                    'message': 'Account is not active'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            if remember_me:
                refresh.set_exp(lifetime=timedelta(days=7))
            
            log_info(f"User logged in successfully", request, {
                'user_id': user.id,
                'username': user.username,
                'remember_me': remember_me
            })
            
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
            log_security(f"Failed login attempt", request, {
                'username_or_email': username_or_email,
                'user_exists': user is not None
            })
            return Response({
                'success': False,
                'message': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            log_warning("Logout attempt without refresh token", request)
            return Response({
                'success': False,
                'message': 'Refresh token is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            log_info("User logged out successfully", request)
            return Response({
                'success': True,
                'message': 'Logout successful'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            log_error(f"Logout failed: {str(e)}", request, {'token_preview': refresh_token[:20]})
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
        log_warning("Password reset request without email", request)
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
            log_info(f"Password reset email sent to {email} | JUST FOR DEV(Verification link): {reset_link}", request, {'user_id': user.id})
        except Exception as e:
            log_error(f"Password reset email failed: {str(e)}", request, {'user_id': user.id, 'email': email})

    # Always return same message for security
    log_info(f"Password reset requested for email: {email}", request, {'user_found': user is not None})
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
                log_warning(f"Expired password reset token for user {user.username}", request)
                return Response({
                    'success': False,
                    'message': 'Password reset token has expired'
                }, status=status.HTTP_400_BAD_REQUEST)

            password = request.data.get('password', '')

            if not all([password]):
                log_warning("Password reset attempt without password", request)
                return Response({
                    'success': False,
                    'message': 'Password is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(password)
            user.password_reset_token = None
            user.password_reset_sent_at = None
            user.save()

            log_audit(f"User password reset successfully", request, {
                'user_id': user.id,
                'username': user.username
            })

            return Response({
                'success': True,
                'message': 'Password reset successfully. You can now login.'
            }, status=status.HTTP_200_OK)

    except Exception as e:
        log_error(f"Password reset failed: {str(e)}", request, {'token': token[:20]})
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
    log_info(f"User viewed their profile", request)
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
    
    log_info(f"User profile viewed: {username}", request, {
        'viewer': request.user.username if request.user.is_authenticated else 'anonymous',
        'is_own_profile': include_sensitive
    })
    
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
            old_email = user.email
            old_username = user.username
            
            serializer.save()
            
            changes = {}
            if old_email != user.email:
                changes['email_changed'] = True
            if old_username != user.username:
                changes['username_changed'] = True
            
            log_audit(f"User updated their profile", request, changes)
            
            return Response({
                'success': True,
                'message': 'Profile updated successfully',
                'user': serializer.data
            }, status=status.HTTP_200_OK)
    
    log_warning(f"Profile update validation failed", request, {'errors': serializer.errors})
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
        log_warning("Profile picture update without file", request)
        return Response({
            'success': False,
            'message': 'No image file provided'
        }, status=status.HTTP_400_BAD_REQUEST)

    profile_picture = request.FILES['profile_picture']
    user = request.user

    # Validate file type
    if not profile_picture.content_type.startswith('image/'):
        log_warning(f"Invalid file type for profile picture: {profile_picture.content_type}", request)
        return Response({
            'success': False,
            'message': 'Only image files are allowed'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Validate file size
    if profile_picture.size > MAX_PROFILE_PICTURE_SIZE:
        log_warning(f"Profile picture too large: {profile_picture.size} bytes", request)
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
            
            log_info(f"User updated profile picture", request, {
                'file_size': profile_picture.size,
                'content_type': profile_picture.content_type
            })
            
            return Response({
                'success': True,
                'message': 'Profile picture updated successfully',
                'profile_picture': user.profile_picture.url
            }, status=status.HTTP_200_OK)

    except Exception as e:
        log_error(f"Profile picture update failed: {str(e)}", request)
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
        log_warning("Attempt to delete non-existent profile picture", request)
        return Response({
            'success': False,
            'message': 'No profile picture to delete'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        with transaction.atomic():
            user.profile_picture.delete(save=False)
            user.profile_picture = None
            user.save()

            log_info("User deleted profile picture", request)
            return Response({
                'success': True,
                'message': 'Profile picture deleted successfully'
            }, status=status.HTTP_200_OK)

    except Exception as e:
        log_error(f"Profile picture deletion failed: {str(e)}", request)
        return Response({
            'success': False,
            'message': 'Failed to delete profile picture'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)