from django.contrib import admin
from .models import Reaction, Comment

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

