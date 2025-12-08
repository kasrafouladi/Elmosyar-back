from django.db import models
from django.conf import settings
import os


class Post(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField(max_length=5000)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='replies')
    category = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    mentions = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='mentioned_in_posts', blank=True)
    tags = models.CharField(max_length=4096, blank=True)
    is_repost = models.BooleanField(default=False)
    original_post = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='reposts')
    
    # فیچر جدید: سیستم ذخیره پست‌ها
    saved_by = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='saved_posts', blank=True)
    
    # فیلد جدید برای ذخیره داده‌های JSON ساختاریافته
    attributes = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', 'created_at']),
            models.Index(fields=['author', 'created_at']),
        ]
        db_table = 'post'

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
        db_table = 'postmedia'

    def __str__(self):
        return f"Media for post {self.post_id} ({self.media_type})"

    def delete(self, *args, **kwargs):
        """حذف فایل فیزیکی هنگام حذف مدیا"""
        if self.file:
            if os.path.isfile(self.file.path):
                os.remove(self.file.path)
        super().delete(*args, **kwargs)


# ════════════════════════════════════════════════════════════
# 📁 Category Format Model
# ════════════════════════════════════════════════════════════

class CategoryFormat(models.Model):
    category = models.CharField(max_length=255, unique=True, db_index=True)
    format_file = models.FileField(upload_to='category_formats/')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'category_format'

    def __str__(self):
        return f"Format for {self.category}"

    def delete(self, *args, **kwargs):
        """حذف فایل فیزیکی هنگام حذف فرمت"""
        if self.format_file:
            if os.path.isfile(self.format_file.path):
                os.remove(self.format_file.path)
        super().delete(*args, **kwargs)