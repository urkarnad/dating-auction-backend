from rest_framework.permissions import BasePermission


class NotBanned(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return not getattr(user, 'is_banned', False)