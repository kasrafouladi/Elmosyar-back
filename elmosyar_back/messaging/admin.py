from django.contrib import admin
from .models import Conversation, Message

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

