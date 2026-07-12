"""
leave/mixins.py
───────────────────────────────────────────────────────────────────────────
Self-contained so this app has no import-order dependency on employees.
If your project already has an equivalent manager-check mixin (e.g.
employees.mixins.StaffManagerRequiredMixin), feel free to delete
ManagerRequiredMixin here and import that one instead — behavior is
identical (superuser or is_staff).
───────────────────────────────────────────────────────────────────────────
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied


class ManagerRequiredMixin(LoginRequiredMixin):
    """Superusers or is_staff only — guards the approve/decline/list views."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, "You do not have permission to manage leave requests.")
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class OwnLeaveRequestMixin(LoginRequiredMixin):
    """
    For staff-facing views: ensures the logged-in user has a linked Staff
    profile before proceeding (needed to apply for or list leave).
    Managers are also allowed through — they can browse their own
    self-service pages too since is_staff accounts often have Staff
    records as well.
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not hasattr(request.user, "staff_profile"):
            messages.error(
                request, "Your account is not linked to a staff profile. Contact HR for access."
            )
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
