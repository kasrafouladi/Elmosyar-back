from rest_framework.permissions import BasePermission

class IsSuperUser(BasePermission):
    """فقط سوپر یوزرها می‌توانند به لاگ‌ها دسترسی داشته باشند"""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)