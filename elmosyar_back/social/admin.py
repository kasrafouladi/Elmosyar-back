from django.contrib import admin
from .models import UserFollow

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

