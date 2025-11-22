from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import (
    User, Post, PostMedia, Reaction, Comment, 
    Notification, Conversation, Message, UserFollow
)


# =====================================================
# User Admin
# =====================================================
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = [
        'username', 'email', 'full_name_display', 
        'is_email_verified', 'is_staff', 'followers_count', 
        'following_count', 'posts_count', 'date_joined'
    ]
    list_filter = [
        'is_email_verified', 'is_staff', 'is_superuser', 
        'is_active', 'date_joined'
    ]
    search_fields = ['username', 'email', 'first_name', 'last_name', 'student_id']
    readonly_fields = ['date_joined', 'last_login', 'created_at', 'updated_at']
    date_hierarchy = 'date_joined'
    
    fieldsets = (
        ('اطلاعات ورود', {
            'fields': ('username', 'password')
        }),
        ('اطلاعات شخصی', {
            'fields': ('email', 'first_name', 'last_name', 'student_id', 'bio', 'profile_picture')
        }),
        ('وضعیت', {
            'fields': ('is_email_verified', 'is_active', 'is_staff', 'is_superuser')
        }),
        ('دسترسی‌ها', {
            'fields': ('groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('تاریخ‌ها', {
            'fields': ('date_joined', 'last_login', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('توکن‌های تایید', {
            'fields': (
                'email_verification_token', 'email_verification_sent_at',
                'password_reset_token', 'password_reset_sent_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        ('ایجاد کاربر جدید', {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )
    
    def full_name_display(self, obj):
        """نمایش نام کامل"""
        full_name = f"{obj.first_name} {obj.last_name}".strip()
        return full_name if full_name else '-'
    full_name_display.short_description = 'نام کامل'


# =====================================================
# Post Admin
# =====================================================
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'author', 'content_preview', 'category', 
        'has_media', 'is_repost', 'likes_count', 
        'dislikes_count', 'comments_count', 'created_at'
    ]
    list_filter = ['category', 'is_repost', 'created_at']
    search_fields = ['content', 'author__username', 'category']
    readonly_fields = ['created_at', 'updated_at', 'likes_count', 'dislikes_count', 'comments_count']
    date_hierarchy = 'created_at'
    filter_horizontal = ['mentions', 'saved_by']
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('author', 'content', 'category', 'tags')
        }),
        ('مدیا', {
            'fields': ('image', 'video'),
            'classes': ('collapse',)
        }),
        ('ریپوست', {
            'fields': ('is_repost', 'original_post'),
            'classes': ('collapse',)
        }),
        ('پاسخ به پست', {
            'fields': ('parent',),
            'classes': ('collapse',)
        }),
        ('منشن‌ها و ذخیره‌ها', {
            'fields': ('mentions', 'saved_by'),
            'classes': ('collapse',)
        }),
        ('آمار', {
            'fields': ('likes_count', 'dislikes_count', 'comments_count'),
            'classes': ('collapse',)
        }),
        ('تاریخ‌ها', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def content_preview(self, obj):
        """نمایش محتوای کوتاه شده"""
        if len(obj.content) > 80:
            return obj.content[:80] + '...'
        return obj.content
    content_preview.short_description = 'محتوا'
    
    def has_media(self, obj):
        """نمایش وضعیت مدیا"""
        has_image = bool(obj.image)
        has_video = bool(obj.video)
        has_extra_media = obj.media.exists()
        
        if has_image or has_video or has_extra_media:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: red;">✗</span>')
    has_media.short_description = 'مدیا'


# =====================================================
# PostMedia Admin
# =====================================================
@admin.register(PostMedia)
class PostMediaAdmin(admin.ModelAdmin):
    list_display = ['id', 'post', 'media_type', 'caption', 'order', 'created_at']
    list_filter = ['media_type', 'created_at']
    search_fields = ['post__content', 'caption']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('اطلاعات مدیا', {
            'fields': ('post', 'file', 'media_type', 'caption', 'order')
        }),
        ('تاریخ', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


# =====================================================
# Reaction Admin
# =====================================================
@admin.register(Reaction)
class ReactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'post', 'reaction', 'created_at']
    list_filter = ['reaction', 'created_at']
    search_fields = ['user__username', 'post__content']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('ری‌اکشن', {
            'fields': ('user', 'post', 'reaction')
        }),
        ('تاریخ', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


# =====================================================
# Comment Admin
# =====================================================
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'post', 'content_preview', 
        'likes_count', 'replies_count', 'created_at'
    ]
    list_filter = ['created_at']
    search_fields = ['content', 'user__username', 'post__content']
    readonly_fields = ['created_at', 'likes_count', 'replies_count']
    date_hierarchy = 'created_at'
    filter_horizontal = ['likes']
    
    fieldsets = (
        ('کامنت', {
            'fields': ('user', 'post', 'content', 'parent')
        }),
        ('لایک‌ها', {
            'fields': ('likes', 'likes_count'),
            'classes': ('collapse',)
        }),
        ('آمار', {
            'fields': ('replies_count',),
            'classes': ('collapse',)
        }),
        ('تاریخ', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def content_preview(self, obj):
        """نمایش محتوای کوتاه شده"""
        if len(obj.content) > 60:
            return obj.content[:60] + '...'
        return obj.content
    content_preview.short_description = 'محتوا'


# =====================================================
# Notification Admin
# =====================================================
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'recipient', 'sender', 'notif_type', 
        'message_preview', 'is_read', 'created_at'
    ]
    list_filter = ['notif_type', 'is_read', 'created_at']
    search_fields = ['recipient__username', 'sender__username', 'message']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('نوتیفیکیشن', {
            'fields': ('recipient', 'sender', 'notif_type', 'message', 'is_read')
        }),
        ('مرتبط با', {
            'fields': ('post', 'comment'),
            'classes': ('collapse',)
        }),
        ('تاریخ', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def message_preview(self, obj):
        """نمایش پیام کوتاه شده"""
        if obj.message:
            if len(obj.message) > 50:
                return obj.message[:50] + '...'
            return obj.message
        return '-'
    message_preview.short_description = 'پیام'
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        """علامت‌گذاری به عنوان خوانده شده"""
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} نوتیفیکیشن به عنوان خوانده شده علامت‌گذاری شد.')
    mark_as_read.short_description = 'علامت‌گذاری به عنوان خوانده شده'
    
    def mark_as_unread(self, request, queryset):
        """علامت‌گذاری به عنوان خوانده نشده"""
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} نوتیفیکیشن به عنوان خوانده نشده علامت‌گذاری شد.')
    mark_as_unread.short_description = 'علامت‌گذاری به عنوان خوانده نشده'


# =====================================================
# UserFollow Admin
# =====================================================
@admin.register(UserFollow)
class UserFollowAdmin(admin.ModelAdmin):
    list_display = ['id', 'follower', 'following', 'created_at']
    list_filter = ['created_at']
    search_fields = ['follower__username', 'following__username']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('فالو', {
            'fields': ('follower', 'following')
        }),
        ('تاریخ', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


# =====================================================
# Conversation Admin
# =====================================================
@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'participants_display', 'messages_count', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['participants__username']
    readonly_fields = ['created_at', 'updated_at', 'messages_count']
    date_hierarchy = 'created_at'
    filter_horizontal = ['participants']
    
    fieldsets = (
        ('مکالمه', {
            'fields': ('participants',)
        }),
        ('آمار', {
            'fields': ('messages_count',),
            'classes': ('collapse',)
        }),
        ('تاریخ‌ها', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def participants_display(self, obj):
        """نمایش شرکت‌کنندگان"""
        participants = list(obj.participants.all()[:3])
        usernames = [p.username for p in participants]
        if obj.participants.count() > 3:
            usernames.append(f'... (+{obj.participants.count() - 3})')
        return ', '.join(usernames)
    participants_display.short_description = 'شرکت‌کنندگان'
    
    def messages_count(self, obj):
        """تعداد پیام‌ها"""
        return obj.messages.count()
    messages_count.short_description = 'تعداد پیام‌ها'


# =====================================================
# Message Admin
# =====================================================
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'sender', 'conversation', 'content_preview', 
        'has_attachment', 'is_read', 'created_at'
    ]
    list_filter = ['is_read', 'created_at']
    search_fields = ['sender__username', 'content']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('پیام', {
            'fields': ('conversation', 'sender', 'content', 'is_read')
        }),
        ('پیوست‌ها', {
            'fields': ('image', 'file'),
            'classes': ('collapse',)
        }),
        ('تاریخ', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def content_preview(self, obj):
        """نمایش محتوای کوتاه شده"""
        if len(obj.content) > 60:
            return obj.content[:60] + '...'
        return obj.content
    content_preview.short_description = 'محتوا'
    
    def has_attachment(self, obj):
        """نمایش وضعیت پیوست"""
        if obj.image or obj.file:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: red;">✗</span>')
    has_attachment.short_description = 'پیوست'
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        """علامت‌گذاری به عنوان خوانده شده"""
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} پیام به عنوان خوانده شده علامت‌گذاری شد.')
    mark_as_read.short_description = 'علامت‌گذاری به عنوان خوانده شده'
    
    def mark_as_unread(self, request, queryset):
        """علامت‌گذاری به عنوان خوانده نشده"""
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} پیام به عنوان خوانده نشده علامت‌گذاری شد.')
    mark_as_unread.short_description = 'علامت‌گذاری به عنوان خوانده نشده'


# =====================================================
# سفارشی‌سازی Admin Site
# =====================================================
admin.site.site_header = 'مدیریت Elmosyar'
admin.site.site_title = 'پنل مدیریت'
admin.site.index_title = 'خوش آمدید به پنل مدیریت Elmosyar'