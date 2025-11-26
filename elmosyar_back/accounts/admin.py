from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

# =====================================================
# User Admin
# =====================================================
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = [
        'username', 'email', 'full_name_display', 
        'is_email_verified', 'is_staff', #'followers_count', 
        #'following_count', 
        'posts_count', 'date_joined'
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
