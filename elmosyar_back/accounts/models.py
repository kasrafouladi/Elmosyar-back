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

    followers = models.ManyToManyField(
        'self', 
        symmetrical=False, 
        related_name='following', 
        blank=True,
        through='UserFollow'
    )

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        db_table = 'core_user'

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
            UserFollow.objects.create(follower=self, following=user)
            return True
        return False

    def unfollow(self, user):
        """آنفالو کردن کاربر"""
        try:
            follow_relation = UserFollow.objects.get(follower=self, following=user)
            follow_relation.delete()
            return True
        except UserFollow.DoesNotExist:
            return False

    @property
    def followers_count(self):
        """تعداد فالوورها"""
        return UserFollow.objects.filter(following=self).count()

    @property
    def following_count(self):
        """تعداد افرادی که کاربر فالو کرده"""
        return UserFollow.objects.filter(follower=self).count()

    @property
    def posts_count(self):
        """تعداد پست‌های کاربر"""
        return self.posts.count()

    @property
    def is_verified(self):
        return self.is_email_verified

