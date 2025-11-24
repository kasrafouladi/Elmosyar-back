from rest_framework import serializers
from accounts.serializers import UserSerializer
from .models import Comment


class CommentSerializer(serializers.ModelSerializer):
    user_info = UserSerializer(source='user', read_only=True)
    likes_count = serializers.SerializerMethodField()
    replies_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            'id', 'user', 'user_info', 'post', 'content', 'created_at',
            'parent', 'likes_count', 'replies_count', 'is_liked'
        ]
        read_only_fields = ['user', 'created_at']

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_replies_count(self, obj):
        return Comment.objects.filter(parent=obj).count()

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(id=request.user.id).exists()
        return False
