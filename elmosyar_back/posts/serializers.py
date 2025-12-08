from rest_framework import serializers
from accounts.serializers import UserSerializer
from .models import Post, PostMedia, CategoryFormat


class PostMediaSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()

    class Meta:
        model = PostMedia
        fields = ['id', 'url', 'media_type', 'caption', 'order', 'file_size']

    def get_url(self, obj):
        return obj.file.url if obj.file else ''

    def get_file_size(self, obj):
        return obj.file.size if obj.file else 0


class PostSerializer(serializers.ModelSerializer):
    author_info = UserSerializer(source='author', read_only=True)
    media = PostMediaSerializer(many=True, read_only=True)
    mentions = UserSerializer(many=True, read_only=True)
    likes_count = serializers.SerializerMethodField()
    dislikes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    reposts_count = serializers.SerializerMethodField()
    replies_count = serializers.SerializerMethodField()
    user_reaction = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    attributes = serializers.JSONField(default=dict, required=False)  # اضافه کردن فیلد attributes

    class Meta:
        model = Post
        fields = [
            'id', 'author', 'author_info', 'content', 'created_at', 'updated_at',
            'tags', 'mentions', 'media', 'category', 'parent', 'is_repost',
            'original_post', 'likes_count', 'dislikes_count', 'comments_count',
            'reposts_count', 'replies_count', 'user_reaction', 'is_saved', 'attributes'
        ]
        read_only_fields = ['author', 'created_at', 'updated_at']

    def get_likes_count(self, obj):
        return obj.reactions.filter(reaction='like').count()

    def get_dislikes_count(self, obj):
        return obj.reactions.filter(reaction='dislike').count()

    def get_comments_count(self, obj):
        return obj.comments.count()

    def get_reposts_count(self, obj):
        return Post.objects.filter(original_post=obj, is_repost=True).count()

    def get_replies_count(self, obj):
        return obj.replies.count()

    def get_user_reaction(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            reaction = obj.reactions.filter(user=request.user).first()
            return reaction.reaction if reaction else None
        return None

    def get_is_saved(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.saved_by.filter(id=request.user.id).exists()
        return False


class CategoryFormatSerializer(serializers.ModelSerializer):
    created_by_info = UserSerializer(source='created_by', read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = CategoryFormat
        fields = ['id', 'category', 'format_file', 'file_url', 'created_by', 'created_by_info', 'created_at', 'updated_at']
        read_only_fields = ['created_by', 'created_at', 'updated_at']

    def get_file_url(self, obj):
        return obj.format_file.url if obj.format_file else ''