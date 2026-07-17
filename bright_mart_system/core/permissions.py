from rest_framework.permissions import BasePermission

class IsCustomerRole(BasePermission):
    """
    Allows access to customers, but gives Superusers an automatic pass.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
            
        # 🌟 THE MASTER PASS: If they are a superuser, let them through immediately
        if request.user.is_superuser:
            return True
            
        # Otherwise, check if they are an actual registered customer
        return hasattr(request.user, 'customer_profile')

class IsStaffRole(BasePermission):
    """
    Allows access to internal staff, and gives Superusers an automatic pass.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
            
        # 🌟 THE MASTER PASS
        if request.user.is_superuser:
            return True
            
        # Otherwise, check if they belong to the Staff group or have the flag
        return request.user.is_staff or request.user.groups.filter(name='Staff').exists()
    
class IsStrictSuperuser(BasePermission):
    """
    Allows access ONLY to accounts that have explicit global superuser status.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)