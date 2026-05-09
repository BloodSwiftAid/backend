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

class IsFacilityVerified(permissions.BasePermission):
    """
    Allows full access only if the facility is verified.
    Otherwise, only allows safe methods (GET, HEAD, OPTIONS).
    """
    message = "Facility not verified. Please contact admin for full access."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        if request.user.role == 'INTERNAL_ADMIN':
            return True
            
        if request.method in permissions.SAFE_METHODS:
            return True
            
        profile = getattr(request.user, 'profile', None)
        if not profile:
            return True
            
        facility = profile.hospital or profile.blood_bank
        if not facility:
            return True
            
        return facility.is_verified
