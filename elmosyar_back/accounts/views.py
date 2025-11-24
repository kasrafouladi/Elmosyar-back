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
import logging

from .models import User
from .serializers import UserSerializer, SignUpSerializer, LoginSerializer, ResendVerificationSerializer

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

