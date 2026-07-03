# from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin

# class StaffManagerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
#     """Ensure only staff users can access HR functions."""
#     def test_func(self):
#         return self.request.user.is_staff or self.request.user.is_superuser



"""
employees/mixins.py
───────────────────────────────────────────────────────────────────────────
Reusable permission mixins for the employees app.

Access rule: only superusers or is_staff users may create/edit staff
records. Regular staff (is_staff=False) may only view their own profile.
───────────────────────────────────────────────────────────────────────────
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


class StaffManagerRequiredMixin(LoginRequiredMixin):
    """
    Allow access only to superusers or staff (is_staff=True).

    Usage:
        class StaffCreateView(StaffManagerRequiredMixin, CreateView):
            ...
    """

    def dispatch(self, request, *args, **kwargs):
        # 1. Must be authenticated (LoginRequiredMixin handles redirect)
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # 2. Must be superuser OR is_staff
        if not (request.user.is_superuser or request.user.is_staff):
            messages.error(
                request,
                "You do not have permission to access this section. "
                "Contact your system administrator.",
            )
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)


class SuperuserRequiredMixin(LoginRequiredMixin):
    """
    Restrict to superusers only (e.g. for delete operations).
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if not request.user.is_superuser:
            messages.error(
                request,
                "Only system administrators can perform this action.",
            )
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)


class OwnProfileOrStaffMixin(LoginRequiredMixin):
    """
    Allow staff managers full access.
    Allow regular staff to view/edit their own profile only.
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # Staff managers see everything
        if request.user.is_staff or request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)

        # Regular user: only their own profile
        obj_uuid = kwargs.get("uuid")
        try:
            own_uuid = str(request.user.staff_profile.uuid)
        except AttributeError:
            raise PermissionDenied

        if obj_uuid != own_uuid:
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)
