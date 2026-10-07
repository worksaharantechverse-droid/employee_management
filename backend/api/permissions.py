from rest_framework.permissions import BasePermission, SAFE_METHODS

def role(user):
    return getattr(user, "role", "").upper()

class RolePermission(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return view.can_access_object(request, obj)

class IsHR(BasePermission):
    def has_permission(self, request, view):
        return role(request.user) == "HR" or request.user.is_superuser
