from rest_framework import permissions

class IsInternalAdmin(permissions.BasePermission):
    """
    Allows access only to internal admin users.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'INTERNAL_ADMIN')

class IsOrganizationAdmin(permissions.BasePermission):
    """
    Allows access only to users who are admins of the organization.
    """
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Internal admin has full access
        if request.user.role == 'INTERNAL_ADMIN':
            return True
            
        # Check if user is an admin of this specific organization
        try:
            profile = request.user.profile
            return profile.organization == obj and request.user.role in ['HOSPITAL_ADMIN', 'BLOODBANK_ADMIN']
        except AttributeError:
            return False
