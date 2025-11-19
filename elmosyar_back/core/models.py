from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.mail import send_mail
from django.conf import settings
import uuid
import os
from datetime import timedelta
from django.utils import timezone

class User(AbstractUser):
    email = models.EmailField(unique=True)
    student_id = models.CharField(max_length=20, blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True, null=True)
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

    # فیچرهای جدید: سیستم فالو
    followers = models.ManyToManyField(
        'self', 
        symmetrical=False, 
        related_name='following', 
        blank=True
    )

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.username

    def generate_email_verification_token(self):
        """تولید توکن برای تأیید ایمیل"""
        self.email_verification_token = str(uuid.uuid4())
        self.email_verification_sent_at = timezone.now()
        self.save()
        return self.email_verification_token

    def generate_password_reset_token(self):
        """تولید توکن برای ریست پسورد"""
        self.password_reset_token = str(uuid.uuid4())
        self.password_reset_sent_at = timezone.now()
        self.save()
        return self.password_reset_token

    def verify_email(self):
        """تأیید ایمیل کاربر"""
        self.is_email_verified = True
        self.email_verification_token = None
        self.email_verification_sent_at = None
        self.save()

    def is_password_reset_token_valid(self):
        """بررسی معتبر بودن توکن ریست پسورد"""
        if not self.password_reset_sent_at:
            return False
        return timezone.now() - self.password_reset_sent_at <= timedelta(hours=1)

    def is_email_verification_token_valid(self):
        """بررسی معتبر بودن توکن تأیید ایمیل"""
        if not self.email_verification_sent_at:
            return False
        return timezone.now() - self.email_verification_sent_at <= timedelta(hours=24)

    def follow(self, user):
        """فالو کردن کاربر دیگر"""
        if user != self and not self.following.filter(id=user.id).exists():
            self.following.add(user)
            return True
        return False

    def unfollow(self, user):
        """آنفالو کردن کاربر"""
        if self.following.filter(id=user.id).exists():
            self.following.remove(user)
            return True
        return False

    @property
    def followers_count(self):
        """تعداد فالوورها"""
        return self.followers.count()

    @property
    def following_count(self):
        """تعداد افرادی که کاربر فالو کرده"""
        return self.following.count()

    @property
    def posts_count(self):
        """تعداد پست‌های کاربر"""
        return self.posts.count()


class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField(max_length=5000)
    image = models.ImageField(upload_to='posts/images/', blank=True, null=True)
    video = models.FileField(upload_to='posts/videos/', blank=True, null=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='replies')
    category = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    mentions = models.ManyToManyField(User, related_name='mentioned_in_posts', blank=True)
    tags = models.CharField(max_length=4096, blank=True)
    is_repost = models.BooleanField(default=False)
    original_post = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='reposts')
    
    # فیچر جدید: سیستم ذخیره پست‌ها
    saved_by = models.ManyToManyField(User, related_name='saved_posts', blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', 'created_at']),
            models.Index(fields=['author', 'created_at']),
        ]

    def __str__(self):
        return f"Post by {self.author} at {self.created_at}"[:50]

    @property
    def likes_count(self):
        """تعداد لایک‌ها"""
        return self.reactions.filter(reaction='like').count()

    @property
    def dislikes_count(self):
        """تعداد دیس‌لایک‌ها"""
        return self.reactions.filter(reaction='dislike').count()

    @property
    def comments_count(self):
        """تعداد کامنت‌ها"""
        return self.comments.count()

    def save(self, *args, **kwargs):
        """ذخیره پست با اعتبارسنجی"""
        if self.parent and self.parent.parent:
            raise ValueError("Cannot reply to a reply")
        super().save(*args, **kwargs)


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
    
    # فیچر جدید: اطلاعات اضافی مدیا
    caption = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"Media for post {self.post_id} ({self.media_type})"

    def delete(self, *args, **kwargs):
        """حذف فایل فیزیکی هنگام حذف مدیا"""
        if self.file:
            if os.path.isfile(self.file.path):
                os.remove(self.file.path)
        super().delete(*args, **kwargs)


class Reaction(models.Model):
    REACTION_CHOICES = [
        ("like", "Like"),
        ("dislike", "Dislike"),
        ("love", "Love"),
        ("laugh", "Laugh"),
        ("sad", "Sad"),
        ("angry", "Angry"),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reactions')
    reaction = models.CharField(max_length=10, choices=REACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')
        indexes = [
            models.Index(fields=['post', 'reaction']),
        ]

    def __str__(self):
        return f"{self.user.username} {self.reaction} on {self.post_id}"


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    
    # فیچر جدید: سیستم لایک برای کامنت‌ها
    likes = models.ManyToManyField(User, related_name='liked_comments', blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment by {self.user} on {self.post_id}"

    @property
    def likes_count(self):
        return self.likes.count()

    @property
    def replies_count(self):
        return self.replies.count()


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

    def __str__(self):
        return f"{self.notif_type} for {self.recipient}"

    def mark_as_read(self):
        """علامت‌گذاری نوتیفیکیشن به عنوان خوانده شده"""
        self.is_read = True
        self.save()


class Conversation(models.Model):
    """مدل جدید برای مکالمات خصوصی"""
    participants = models.ManyToManyField(User, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Conversation {self.id}"


class Message(models.Model):
    """مدل جدید برای پیام‌های خصوصی"""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(max_length=2000)
    image = models.ImageField(upload_to='messages/images/', blank=True, null=True)
    file = models.FileField(upload_to='messages/files/', blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'is_read', 'created_at']),
        ]

    def __str__(self):
        return f"Message from {self.sender} in {self.conversation.id}"

    def mark_as_read(self):
        """علامت‌گذاری پیام به عنوان خوانده شده"""
        self.is_read = True
        self.save()