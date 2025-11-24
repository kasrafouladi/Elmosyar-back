from rest_framework import serializers
from accounts.serializers import UserSerializer
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    sender_info = UserSerializer(source='sender', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'sender', 'sender_info', 'notif_type', 'post', 'comment',
            'message', 'is_read', 'created_at'
        ]
        read_only_fields = ['created_at']

