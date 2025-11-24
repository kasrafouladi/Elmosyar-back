from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User


class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
            if user.is_email_verified:
                raise serializers.ValidationError("Email is already verified.")
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
        return value

class UserSerializer(serializers.ModelSerializer):
    followers_count = serializers.ReadOnlyField()
    following_count = serializers.ReadOnlyField()
    posts_count = serializers.ReadOnlyField()
    is_following = serializers.SerializerMethodField()
    is_me = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'profile_picture', 'bio', 'student_id', 'is_email_verified',
            'followers_count', 'following_count', 'posts_count',
            'is_following', 'is_me', 'created_at'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'password': {'write_only': True}
        }

    def get_is_following(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return UserFollow.objects.filter(follower=request.user, following=obj).exists()
        return False

    def get_is_me(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user.id == obj.id
        return False

class SignUpSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2']
    
    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('Email has already been used!')
        return value
    
    def validate_password(self, value):
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value
            
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError("Passwords do not match!")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.is_active = False  # نیاز به تأیید ایمیل
        user.save()
        return user

class LoginSerializer(serializers.Serializer):
    username_or_email = serializers.CharField(required=True)
    password = serializers.CharField(required=True)
    rememberMe = serializers.BooleanField(default=False)