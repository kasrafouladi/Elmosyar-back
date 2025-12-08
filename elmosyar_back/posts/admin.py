from django.contrib import admin
from django.utils.html import format_html
from .models import Post, PostMedia, CategoryFormat


# =====================================================
# Inline برای PostMedia
# =====================================================
class PostMediaInline(admin.TabularInline):
    model = PostMedia
    extra = 1
    fields = ['file', 'media_type', 'caption', 'order']
    readonly_fields = ['created_at']


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
    inlines = [PostMediaInline]
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('author', 'content', 'category', 'tags', 'attributes')
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
        has_extra_media = obj.media.exists()
        
        if has_extra_media:
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
# CategoryFormat Admin 
# =====================================================
@admin.register(CategoryFormat)
class CategoryFormatAdmin(admin.ModelAdmin):
    list_display = ['category', 'created_by', 'created_at', 'updated_at']
    list_filter = ['created_at']
    search_fields = ['category', 'created_by__username']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('اطلاعات فرمت', {
            'fields': ('category', 'format_file', 'created_by')
        }),
        ('تاریخ‌ها', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )