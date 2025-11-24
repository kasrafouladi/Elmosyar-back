from django.contrib import admin
from .models import Notification

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

