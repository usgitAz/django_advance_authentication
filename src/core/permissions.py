from rest_framework.permissions import BasePermission


class IsOwnerOrStaff(BasePermission):
    def has_object_permission(self, request, view, obj):
        """Allow access to object if user is owner or staff."""
        return bool(request.user.is_staff or request.user == obj)
