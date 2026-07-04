"""
employees/views.py
───────────────────────────────────────────────────────────────────────────
Staff management views.

Access control
──────────────
  Create / Update / List (all)  →  is_staff OR is_superuser
  Delete                        →  is_superuser only
  Detail                        →  is_staff / is_superuser  OR own profile

All views use Class-Based Views.
Business logic (e.g. generating employee_no) lives in the model's save().
Views are deliberately thin — they orchestrate, not compute.
───────────────────────────────────────────────────────────────────────────
"""

from django.contrib import messages
from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    UpdateView,
    View,
)

from .forms import StaffProfileForm, StaffUserForm
from .mixins import OwnProfileOrStaffMixin, StaffManagerRequiredMixin, SuperuserRequiredMixin
from .models import Staff, EmploymentStatus


# ─────────────────────────────────────────────────────────────────────────────
# Staff List
# ─────────────────────────────────────────────────────────────────────────────

class StaffListView(StaffManagerRequiredMixin, ListView):
    """
    Paginated list of all staff with search and status filtering.
    URL: /staff/
    """

    model = Staff
    template_name = "employees/staff_list.html"
    context_object_name = "staff_list"
    paginate_by = 25

    def get_queryset(self):
        qs = (
            Staff.objects
            .select_related("user", "staff_rank")
            .prefetch_related("deployments")
            .filter(is_active=True)
        )

        # Search: name, employee_no, email
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                models_Q(
                    user__first_name__icontains=q
                ) | models_Q(
                    user__last_name__icontains=q
                ) | models_Q(
                    employee_no__icontains=q
                ) | models_Q(
                    official_email__icontains=q
                ) | models_Q(
                    phone_mobile__icontains=q
                )
            )

        # Status filter
        status = self.request.GET.get("status", "").strip()
        if status:
            qs = qs.filter(employment_status=status)

        return qs.order_by("user__last_name", "user__first_name")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"]              = self.request.GET.get("q", "")
        ctx["status_filter"]  = self.request.GET.get("status", "")
        ctx["status_choices"] = EmploymentStatus.choices
        ctx["total_count"]    = Staff.objects.filter(is_active=True).count()
        ctx["active_count"]   = Staff.objects.filter(
            is_active=True, employment_status=EmploymentStatus.ACTIVE
        ).count()
        ctx["suspended_count"] = Staff.objects.filter(
            is_active=True, employment_status=EmploymentStatus.SUSPENDED
        ).count()
        # Page header context
        ctx["page_title"]    = "Staff Management"
        ctx["page_subtitle"] = "All registered staff members"
        ctx["breadcrumb"]    = "Staff Management"
        return ctx


# We need Q for the search filter — import it properly
from django.db.models import Q as models_Q


# ─────────────────────────────────────────────────────────────────────────────
# Staff Create
# ─────────────────────────────────────────────────────────────────────────────

class StaffCreateView(StaffManagerRequiredMixin, View):
    """
    Registers a new staff member.

    Handles two forms simultaneously:
      1. StaffUserForm   — creates the Django User account
      2. StaffProfileForm — creates the Staff profile linked to that user

    Both forms are validated atomically. If either fails, nothing is saved.
    URL: /staff/add/
    """

    template_name = "employees/staff_form.html"

    def get(self, request, *args, **kwargs):
        user_form    = StaffUserForm(is_create=True)
        profile_form = StaffProfileForm()
        return self._render(request, user_form, profile_form)

    def post(self, request, *args, **kwargs):
        user_form    = StaffUserForm(request.POST, is_create=True)
        profile_form = StaffProfileForm(request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            try:
                with transaction.atomic():
                    # 1. Save User
                    user = user_form.save(commit=False)
                    user.is_active = True
                    user.is_staff  = False   # Portal staff, not Django admin staff
                    user.save()

                    # 2. Save Staff profile, linking to user
                    staff = profile_form.save(commit=False)
                    staff.user       = user
                    staff.created_by = request.user
                    staff.updated_by = request.user
                    staff.save()

                messages.success(
                    request,
                    f"Staff member <strong>{staff.full_name}</strong> "
                    f"({staff.employee_no}) has been registered successfully.",
                )
                return redirect("employees:detail", uuid=str(staff.uuid))

            except Exception as exc:
                messages.error(
                    request,
                    f"An unexpected error occurred while saving: {exc}. "
                    "Please try again.",
                )

        else:
            # Collect which tabs have errors for front-end tab switching
            messages.error(
                request,
                "Please correct the errors below before saving.",
            )

        return self._render(request, user_form, profile_form)

    def _render(self, request, user_form, profile_form):
        from django.shortcuts import render
        return render(request, self.template_name, {
            "user_form":    user_form,
            "profile_form": profile_form,
            "is_create":    True,
            "page_title":   "Add New Staff",
            "page_subtitle":"Complete all required sections to register a new staff member.",
            "breadcrumb":   "Add New Staff",
        })


# ─────────────────────────────────────────────────────────────────────────────
# Staff Update
# ─────────────────────────────────────────────────────────────────────────────

class StaffUpdateView(StaffManagerRequiredMixin, View):
    """
    Edit an existing staff member's record.
    URL: /staff/<uuid>/edit/
    """

    template_name = "employees/staff_form.html"

    def _get_staff(self, uuid):
        return get_object_or_404(Staff.objects.select_related("user"), uuid=uuid)

    def get(self, request, uuid, *args, **kwargs):
        staff        = self._get_staff(uuid)
        user_form    = StaffUserForm(instance=staff.user, is_create=False)
        profile_form = StaffProfileForm(instance=staff)
        return self._render(request, user_form, profile_form, staff)

    def post(self, request, uuid, *args, **kwargs):
        staff        = self._get_staff(uuid)
        user_form    = StaffUserForm(
            request.POST, instance=staff.user, is_create=False
        )
        profile_form = StaffProfileForm(request.POST, instance=staff)

        if user_form.is_valid() and profile_form.is_valid():
            try:
                with transaction.atomic():
                    user_form.save()

                    staff = profile_form.save(commit=False)
                    staff.updated_by = request.user
                    staff.save()

                messages.success(
                    request,
                    f"<strong>{staff.full_name}</strong>'s record has been updated.",
                )
                return redirect("employees:detail", uuid=str(staff.uuid))

            except Exception as exc:
                messages.error(request, f"Update failed: {exc}")

        else:
            messages.error(request, "Please correct the errors below.")

        return self._render(request, user_form, profile_form, staff)


    def _render(self, request, user_form, profile_form, staff):
        from django.shortcuts import render

        required_fields = [
            "First Name",
            "Last Name",
            "Username",
            "Gender",
            "Date of Birth",
            "State of Origin",
            "Mobile Phone",
            "Employment Type",
            "Employment Status",
            "Date Employed",
        ]

        return render(
            request,
            self.template_name,
            {
                "user_form": user_form,
                "profile_form": profile_form,
                "staff": staff,

                # tells the template this is EDIT mode
                "is_create": False,

                "page_title": f"Edit {staff.full_name}",
                "page_subtitle": f"Employee No: {staff.employee_no}",
                "breadcrumb": "Edit Staff",

                "required_fields": required_fields,
            },
        )

# ─────────────────────────────────────────────────────────────────────────────
# Staff Detail
# ─────────────────────────────────────────────────────────────────────────────

# class StaffDetailView(OwnProfileOrStaffMixin, DetailView):
#     """
#     Read-only staff profile page.
#     URL: /staff/<uuid>/
#     """

#     model = Staff
#     template_name     = "employees/staff_detail.html"
#     context_object_name = "staff"
#     slug_field        = "uuid"
#     slug_url_kwarg    = "uuid"

#     def get_queryset(self):
#         return Staff.objects.select_related(
#             "user", "staff_rank", "created_by", "updated_by"
#         ).prefetch_related("deployments__company", "deployments__department")

#     def get_context_data(self, **kwargs):
#         ctx = super().get_context_data(**kwargs)
#         staff = self.object
#         ctx["page_title"]    = staff.full_name
#         ctx["page_subtitle"] = f"Employee No: {staff.employee_no}"
#         ctx["breadcrumb"]    = "Staff Profile"
#         ctx["can_edit"]      = (
#             self.request.user.is_staff or self.request.user.is_superuser
#         )
#         ctx["deployment"] = staff.current_deployment
#         return ctx


class StaffDetailView(OwnProfileOrStaffMixin, DetailView):
    model = Staff
    context_object_name = "staff"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_template_names(self):
        if self.request.user.is_staff or self.request.user.is_superuser:
            return ["employees/staff_detail.html"]          # extends dashboard/base.html
        return ["employees/staff_detail_self.html"]     # extends dashboard/base_employee.html

    def get_queryset(self):
        return (
            Staff.objects.select_related(
                "user",
                "staff_rank",
                "created_by",
                "updated_by",
            )
            .prefetch_related(
                "deployments__company",
                "deployments__department",
            )
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        staff = self.object

        ctx["page_title"] = staff.full_name
        ctx["page_subtitle"] = f"Employee No: {staff.employee_no}"
        ctx["breadcrumb"] = "Staff Profile"
        ctx["deployment"] = staff.current_deployment
        ctx["can_edit"] = (
            self.request.user.is_staff or self.request.user.is_superuser
        )

        return ctx


# ─────────────────────────────────────────────────────────────────────────────
# Staff Deactivate (Soft Delete)
# ─────────────────────────────────────────────────────────────────────────────

class StaffDeactivateView(SuperuserRequiredMixin, View):
    """
    Soft-deactivates a staff record (sets is_active=False, status=Terminated).
    Hard delete is intentionally never exposed in the portal — use Django admin.
    URL: /staff/<uuid>/deactivate/   [POST only]
    """

    def post(self, request, uuid, *args, **kwargs):
        staff = get_object_or_404(Staff, uuid=uuid)

        with transaction.atomic():
            staff.is_active        = False
            staff.employment_status = EmploymentStatus.TERMINATED
            staff.updated_by        = request.user
            staff.save(update_fields=["is_active", "employment_status", "updated_by", "updated"])

            # Also deactivate the Django user account
            staff.user.is_active = False
            staff.user.save(update_fields=["is_active"])

        messages.warning(
            request,
            f"<strong>{staff.full_name}</strong> ({staff.employee_no}) "
            "has been deactivated. Their login access has been revoked.",
        )
        return redirect("employees:employees-list")


# ─────────────────────────────────────────────────────────────────────────────
# Staff Status Toggle  (suspend / reinstate)
# ─────────────────────────────────────────────────────────────────────────────

class StaffStatusToggleView(StaffManagerRequiredMixin, View):
    """
    Quick-action: toggle employment_status between ACTIVE and SUSPENDED.
    URL: /staff/<uuid>/toggle-status/   [POST only]
    """

    def post(self, request, uuid, *args, **kwargs):
        staff  = get_object_or_404(Staff, uuid=uuid, is_active=True)
        reason = request.POST.get("reason", "").strip()

        if staff.employment_status == EmploymentStatus.ACTIVE:
            staff.employment_status = EmploymentStatus.SUSPENDED
            verb = "suspended"
        else:
            staff.employment_status = EmploymentStatus.ACTIVE
            verb = "reinstated"

        staff.updated_by = request.user
        staff.save(update_fields=["employment_status", "updated_by", "updated"])

        messages.success(
            request,
            f"<strong>{staff.full_name}</strong> has been {verb}."
            + (f" Reason: {reason}" if reason else ""),
        )
        return redirect("employees:detail", uuid=str(staff.uuid))



"""
idcards/views.py
───────────────────────────────────────────────────────────────────────────
Views are deliberately thin — all business logic lives in services.py.

  IDCardDetailView   — on-screen view inside the app shell (base.html),
                        with Print / Reissue / Revoke actions for managers.
  IDCardPrintView    — chrome-free, print-ready card (front + back).
                        Browser "Print → Save as PDF" is the export path,
                        so no server-side PDF library is required and the
                        feature works unchanged on every hosting tier.
  IDCardReissueView  — POST-only, managers only.
  IDCardRevokeView   — POST-only, managers only.
───────────────────────────────────────────────────────────────────────────
"""
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView, View

from employees.models import Staff

from .mixins import ManagerRequiredMixin, OwnCardOrManagerMixin
from .models import StaffIDCard
from .services import IDCardService


class StaffTemplateMixin:

    admin_template = 'employees/id_card.html'
    employee_template = 'employees/id_card_self.html'

    def get_template_names(self):
        if self.request.user.is_superuser or self.request.user.is_staff:
            return [self.admin_template]

        return [self.employee_template]


class IDCardDetailView(StaffTemplateMixin, OwnCardOrManagerMixin, DetailView):
    """URL: /employees/<uuid:staff_uuid>/  (name: idcards:view)"""

    model = StaffIDCard
    template_name = "employees/id_card.html"
    context_object_name = "id_card"

    def get_object(self, queryset=None) -> StaffIDCard:
        staff = get_object_or_404(
            Staff.objects.select_related("user", "staff_rank"),
            uuid=self.kwargs["staff_uuid"],
        )
        self.staff = staff
        # Safety net for staff records created before this module existed —
        # issue_card() is idempotent (get_or_create), so this never
        # duplicates a card for staff created normally via the signal.
        return IDCardService.issue_card(staff=staff)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["staff"] = self.staff
        ctx["can_manage"] = self.request.user.is_staff or self.request.user.is_superuser
        ctx["page_title"] = f"ID Card — {self.staff.full_name}"
        ctx["page_subtitle"] = f"Employee No: {self.staff.employee_no}"
        ctx["breadcrumb"] = "Staff ID Card"
        return ctx


class IDCardPrintView(StaffTemplateMixin, OwnCardOrManagerMixin, View):
    """
    Standalone A4/CR80-ready print view — opens in a new tab.
    URL: /employees/<uuid:staff_uuid>/print/  (name: idcards:print)
    """

    def get(self, request, staff_uuid, *args, **kwargs):
        staff = get_object_or_404(Staff.objects.select_related("user"), uuid=staff_uuid)
        card = IDCardService.issue_card(staff=staff)
        card.mark_printed()
        return render(
            request,
            "employees/id_card_print.html",
            {"staff": staff, "id_card": card},
        )


class IDCardReissueView(ManagerRequiredMixin, View):
    """POST only. URL: /employees/<uuid:staff_uuid>/reissue/"""

    def post(self, request, staff_uuid, *args, **kwargs):
        staff = get_object_or_404(Staff, uuid=staff_uuid)
        reason = request.POST.get("reason", "").strip()
        IDCardService.reissue_card(staff, issued_by=request.user, reason=reason)
        messages.success(
            request, f"A new ID card has been issued for <strong>{staff.full_name}</strong>."
        )
        return redirect("employees:view", staff_uuid=staff.uuid)


class IDCardRevokeView(ManagerRequiredMixin, View):
    """POST only. URL: /employees/<uuid:staff_uuid>/revoke/"""

    def post(self, request, staff_uuid, *args, **kwargs):
        staff = get_object_or_404(Staff, uuid=staff_uuid)
        reason = request.POST.get("reason", "").strip()
        IDCardService.revoke_card(staff, revoked_by=request.user, reason=reason)
        messages.warning(
            request, f"<strong>{staff.full_name}</strong>'s ID card has been revoked."
        )
        return redirect("employees:view", staff_uuid=staff.uuid)

