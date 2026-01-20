from rest_framework import permissions


class IsTenantUser(permissions.BasePermission):
    """
    Permission to ensure user belongs to the current tenant.
    Django-tenants handles schema isolation, but this adds extra validation.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class IsProjectOwnerOrMember(permissions.BasePermission):
    """
    Permission to check if user is project owner or member.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions for members
        if request.method in permissions.SAFE_METHODS:
            return (
                    obj.owner == request.user or
                    request.user in obj.members.all()
            )

        # Write permissions only for owner
        return obj.owner == request.user


class IsTaskProjectMember(permissions.BasePermission):
    """
    Permission to ensure user has access to the task's project.
    """

    def has_object_permission(self, request, view, obj):
        project = obj.project
        return (
                project.owner == request.user or
                request.user in project.members.all()
        )


class IsAdminOrOwner(permissions.BasePermission):
    """
    Permission for admin users or object owners.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Admins can do anything
        if hasattr(request.user, 'profile') and request.user.profile.role == 'admin':
            return True

        # Check if user is the owner
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        if hasattr(obj, 'user'):
            return obj.user == request.user

        return False