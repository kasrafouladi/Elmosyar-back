from django.db import models
from django.conf import settings
from posts.models import Post


class Reaction(models.Model):
    REACTION_CHOICES = [
        ("like", "Like"),
        ("dislike", "Dislike"),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reactions')
    reaction = models.CharField(max_length=10, choices=REACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')
        indexes = [
            models.Index(fields=['post', 'reaction']),
        ]
        db_table = 'reaction'

    def __str__(self):
        return f"{self.user.username} {self.reaction} on {self.post_id}"


class Comment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    
    # فیچر جدید: سیستم لایک برای کامنت‌ها
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='liked_comments', blank=True)

    class Meta:
        ordering = ['-created_at']
        db_table = 'comment'

    def __str__(self):
        return f"Comment by {self.user} on {self.post_id}"

    @property
    def likes_count(self):
        return self.likes.count()

    @property
    def replies_count(self):
        return self.replies.count()