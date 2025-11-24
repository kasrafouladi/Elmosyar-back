from django.db import models
from django.conf import settings
from posts.models import Post
from interactions.models import Comment


class Notification(models.Model):
    NOTIF_TYPE_CHOICES = [
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('mention', 'Mention'),
        ('repost', 'Repost'),
        ('follow', 'Follow'),
        ('reply', 'Reply'),
    ]
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications')
    notif_type = models.CharField(max_length=20, choices=NOTIF_TYPE_CHOICES)
    post = models.ForeignKey(Post, null=True, blank=True, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, null=True, blank=True, on_delete=models.CASCADE)
    message = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read', 'created_at']),
        ]
        db_table = 'core_notification'

    def __str__(self):
        return f"{self.notif_type} for {self.recipient}"

    def mark_as_read(self):
        """علامت‌گذاری نوتیفیکیشن به عنوان خوانده شده"""
        self.is_read = True
        self.save()

