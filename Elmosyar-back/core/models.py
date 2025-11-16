from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
import random
import string



class User(AbstractUser):
    email = models.EmailField(unique=True)
    student_id = models.CharField(max_length=20, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=255, blank=True, null=True)
    email_verification_sent_at = models.DateTimeField(blank=True, null=True)
    password_reset_token = models.CharField(max_length=255, blank=True, null=True)
    password_reset_sent_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.username

    def generate_email_verification_token(self):
        self.email_verification_token = str(uuid.uuid4())
        return self.email_verification_token

    def generate_password_reset_token(self):
        self.password_reset_token = str(uuid.uuid4())
        return self.password_reset_token

    def verify_email(self):
        self.is_email_verified = True
        self.email_verification_token = None
        self.save()

# --- LinkedIn-like Post System ---
class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField()
    image = models.ImageField(upload_to='posts/images/', blank=True, null=True)
    video = models.FileField(upload_to='posts/videos/', blank=True, null=True)
    # Parent post: if this post is a reply to another post
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='replies')
    # Category ID: posts can belong to categories/rooms (string id)
    category = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    mentions = models.ManyToManyField(User, related_name='mentioned_in_posts', blank=True)
    tags = models.CharField(max_length=4096, blank=True)  # comma separated tags
    is_repost = models.BooleanField(default=False)
    original_post = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='reposts')

    def __str__(self):
        return f"Post by {self.author} at {self.created_at}"[:50]

class PostMedia(models.Model):
    MEDIA_TYPE_CHOICES = [
        ("image", "Image"),
        ("video", "Video"),
        ("audio", "Audio"),
        ("file", "File"),
    ]
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='media')
    file = models.FileField(upload_to='posts/media/')
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Media for post {self.post_id} ({self.media_type})"

class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('user', 'post')


class Reaction(models.Model):
    REACTION_CHOICES = [
        ("like", "Like"),
        ("dislike", "Dislike"),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reactions')
    reaction = models.CharField(max_length=10, choices=REACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # one reaction per user per post (type can be changed)
        unique_together = ('user', 'post')

    def __str__(self):
        return f"{self.user.username} {self.reaction} on {self.post_id}"

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')

class Notification(models.Model):
    NOTIF_TYPE_CHOICES = [
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('mention', 'Mention'),
        ('repost', 'Repost'),
        ('follow', 'Follow'),
    ]
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications')
    notif_type = models.CharField(max_length=20, choices=NOTIF_TYPE_CHOICES)
    post = models.ForeignKey(Post, null=True, blank=True, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, null=True, blank=True, on_delete=models.CASCADE)
    message = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.notif_type} for {self.recipient}"
