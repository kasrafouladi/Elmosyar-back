from rest_framework import serializers
from accounts.serializers import UserSerializer
from .models import Conversation, Message

class MessageSerializer(serializers.ModelSerializer):
    sender_info = UserSerializer(source='sender', read_only=True)

    class Meta:
        model = Message
        fields = [
            'id', 'sender', 'sender_info', 'content', 'image', 'file',
            'is_read', 'created_at'
        ]
        read_only_fields = ['sender', 'created_at']

class ConversationSerializer(serializers.ModelSerializer):
    other_user = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'other_user', 'last_message', 'unread_count', 'updated_at']
        read_only_fields = ['updated_at']

    def get_other_user(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            other_user = obj.participants.exclude(id=request.user.id).first()
            return UserSerializer(other_user, context=self.context).data if other_user else None
        return None

    def get_last_message(self, obj):
        last_message = obj.messages.last()
        if last_message:
            return {
                'content': last_message.content,
                'sender': last_message.sender.username,
                'created_at': last_message.created_at,
                'is_read': last_message.is_read
            }
        return None

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.messages.filter(is_read=False).exclude(sender=request.user).count()
        return 0