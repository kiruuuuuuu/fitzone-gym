from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import AccessMixin


class StaffRequiredMixin(AccessMixin):
    """Verify that the current user is staff"""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_staff:
            raise PermissionDenied("You do not have permission to access this page.")
        return super().dispatch(request, *args, **kwargs)


class TrainerRequiredMixin(AccessMixin):
    """Verify that the current user is a trainer"""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not hasattr(request.user, 'trainer_profile'):
            raise PermissionDenied("You must be a trainer to access this page.")
        return super().dispatch(request, *args, **kwargs)


class SuperuserRequiredMixin(AccessMixin):
    """Verify that the current user is a superuser (admin)"""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_superuser:
            raise PermissionDenied("You must be an administrator to access this page.")
        return super().dispatch(request, *args, **kwargs)

