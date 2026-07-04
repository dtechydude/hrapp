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


# class OwnProfileOrStaffMixin(LoginRequiredMixin):
#     """
#     Allow staff managers full access.
#     Allow regular staff to view/edit their own profile only.
#     """

#     def dispatch(self, request, *args, **kwargs):
#         if not request.user.is_authenticated:
#             return self.handle_no_permission()

#         # Staff managers see everything
#         if request.user.is_staff or request.user.is_superuser:
#             return super().dispatch(request, *args, **kwargs)

#         # Regular user: only their own profile
#         obj_uuid = kwargs.get("uuid")
#         try:
#             own_uuid = str(request.user.staff_profile.uuid)
#         except AttributeError:
#             raise PermissionDenied

#         if obj_uuid != own_uuid:
#             raise PermissionDenied

#         return super().dispatch(request, *args, **kwargs)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied

from .models import Staff


class OwnProfileOrStaffMixin(LoginRequiredMixin):
    """
    HR/Admin:
        Can access every employee profile.

    Employee:
        Can only access their own profile.
    """

    def dispatch(self, request, *args, **kwargs):

        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if request.user.is_staff or request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)

        staff = Staff.objects.filter(
            uuid=kwargs.get("uuid")
        ).select_related("user").first()

        if not staff:
            raise PermissionDenied

        if staff.user != request.user:
            raise PermissionDenied(
                "You may only view your own profile."
            )

        return super().dispatch(request, *args, **kwargs)

"""
idcards/mixins.py
───────────────────────────────────────────────────────────────────────────
Access rule for ID cards (mirrors employees/mixins.py):

  • Superuser / is_staff (HR, Payroll, Branch Manager portal accounts)
      → may view, print, reissue, or revoke ANY staff member's card.
  • Regular staff (is_staff=False, the employee's own login)
      → may view and print ONLY their own card. No reissue/revoke.
───────────────────────────────────────────────────────────────────────────
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied


class OwnCardOrManagerMixin(LoginRequiredMixin):
    """
    Expects the URL kwarg `staff_uuid`. Resolves "own card" via
    request.user.staff_profile — the OneToOne reverse accessor from
    Staff.user (see employees/mixins.py for the identical pattern used
    on staff profiles).
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if request.user.is_staff or request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)

        target_uuid = str(kwargs.get("staff_uuid"))
        try:
            own_uuid = str(request.user.staff_profile.uuid)
        except AttributeError:
            raise PermissionDenied(
                "No staff profile is linked to this account."
            )

        if target_uuid != own_uuid:
            messages.error(request, "You may only view your own ID card.")
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)


class ManagerRequiredMixin(LoginRequiredMixin):
    """Superusers or is_staff only — guards reissue / revoke actions."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(
                request, "You do not have permission to manage ID cards."
            )
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)

