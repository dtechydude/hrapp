"""
leave/views.py
───────────────────────────────────────────────────────────────────────────
Employee-facing:
  LeaveRequestCreateView   — apply for leave
  MyLeaveRequestListView   — "My Leave" — own requests + own balances
  LeaveRequestCancelView   — withdraw a still-Pending request (POST only)

Manager-facing (superuser or is_staff):
  LeaveRequestListView     — all requests, filterable by status, searchable
  LeaveRequestDetailView   — full detail + Approve/Decline actions
  LeaveRequestApproveView  — POST only
  LeaveRequestDeclineView  — POST only

Views stay thin — all balance math and status-transition rules live in
services.py.
───────────────────────────────────────────────────────────────────────────
"""
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import CreateView, DetailView, ListView, View

from . import services
from .forms import LeaveRequestForm
from .mixins import ManagerRequiredMixin, OwnLeaveRequestMixin
from .models import LeaveBalance, LeaveRequest, LeaveRequestStatus


# ═══════════════════════════════════════════════════════════════════════
# Employee-facing
# ═══════════════════════════════════════════════════════════════════════

class LeaveRequestCreateView(OwnLeaveRequestMixin, CreateView):
    """URL: /leave/apply/  (name: leave:apply)"""

    model = LeaveRequest
    form_class = LeaveRequestForm
    template_name = "leave/request_form.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Apply for Leave"
        ctx["breadcrumb"] = "Apply for Leave"
        ctx["balances"] = LeaveBalance.objects.filter(
            staff=self.request.user.staff_profile
        ).select_related("leave_type")
        return ctx

    def form_valid(self, form):
        staff = self.request.user.staff_profile
        try:
            services.submit_request(
                staff=staff,
                leave_type=form.cleaned_data["leave_type"],
                start_date=form.cleaned_data["start_date"],
                end_date=form.cleaned_data["end_date"],
                reason=form.cleaned_data["reason"],
            )
        except ValidationError as exc:
            form.add_error(None, exc.message if hasattr(exc, "message") else str(exc))
            return self.form_invalid(form)

        messages.success(self.request, "Your leave request has been submitted and is pending approval.")
        return redirect("leave:my_requests")


class MyLeaveRequestListView(OwnLeaveRequestMixin, ListView):
    """URL: /leave/my/  (name: leave:my_requests)"""

    model = LeaveRequest
    template_name = "leave/my_requests.html"
    context_object_name = "requests"
    paginate_by = 15

    def get_queryset(self):
        return (
            LeaveRequest.objects.filter(staff=self.request.user.staff_profile)
            .select_related("leave_type")
            .order_by("-applied_at")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "My Leave"
        ctx["breadcrumb"] = "My Leave"
        ctx["balances"] = LeaveBalance.objects.filter(
            staff=self.request.user.staff_profile
        ).select_related("leave_type")
        return ctx


class LeaveRequestCancelView(OwnLeaveRequestMixin, View):
    """POST only. URL: /leave/<uuid>/cancel/  (name: leave:cancel)"""

    def post(self, request, uuid, *args, **kwargs):
        leave_request = get_object_or_404(LeaveRequest, uuid=uuid, staff=request.user.staff_profile)
        try:
            services.cancel_request(leave_request, cancelled_by=request.user)
            messages.success(request, "Your leave request has been withdrawn.")
        except ValidationError as exc:
            messages.error(request, str(exc))
        return redirect("leave:my_requests")


# ═══════════════════════════════════════════════════════════════════════
# Manager-facing
# ═══════════════════════════════════════════════════════════════════════

class LeaveRequestListView(ManagerRequiredMixin, ListView):
    """
    URL: /leave/requests/  (name: leave:list)
    Query params: ?status=Pending|Approved|Declined|Cancelled  &q=search
    """

    model = LeaveRequest
    template_name = "leave/request_list.html"
    context_object_name = "requests"
    paginate_by = 20

    def get_queryset(self):
        qs = LeaveRequest.objects.select_related("staff", "staff__user", "leave_type").order_by("-applied_at")

        status = self.request.GET.get("status", "").strip()
        if status in LeaveRequestStatus.values:
            qs = qs.filter(status=status)

        query = self.request.GET.get("q", "").strip()
        if query:
            qs = qs.filter(
                Q(staff__user__first_name__icontains=query)
                | Q(staff__user__last_name__icontains=query)
                | Q(staff__employee_no__icontains=query)
            )

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Leave Requests"
        ctx["breadcrumb"] = "Leave Requests"
        ctx["current_status"] = self.request.GET.get("status", "")
        ctx["query"] = self.request.GET.get("q", "")
        ctx["status_choices"] = LeaveRequestStatus.choices
        ctx["pending_count"] = LeaveRequest.objects.filter(status=LeaveRequestStatus.PENDING).count()
        return ctx


class LeaveRequestDetailView(ManagerRequiredMixin, DetailView):
    """URL: /leave/<uuid>/  (name: leave:detail)"""

    model = LeaveRequest
    template_name = "leave/request_detail.html"
    context_object_name = "leave_request"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        leave_request = self.object
        ctx["page_title"] = "Leave Request Detail"
        ctx["breadcrumb"] = "Leave Request Detail"
        ctx["balance"] = LeaveBalance.objects.filter(
            staff=leave_request.staff,
            leave_type=leave_request.leave_type,
            year=leave_request.start_date.year,
        ).first()
        return ctx


class LeaveRequestApproveView(ManagerRequiredMixin, View):
    """POST only. URL: /leave/<uuid>/approve/  (name: leave:approve)"""

    def post(self, request, uuid, *args, **kwargs):
        leave_request = get_object_or_404(LeaveRequest, uuid=uuid)
        note = request.POST.get("note", "").strip()
        try:
            services.approve_request(leave_request, approved_by=request.user, note=note)
            messages.success(
                request, f"Leave request for {leave_request.staff.full_name} has been approved."
            )
        except ValidationError as exc:
            messages.error(request, str(exc))
        return redirect("leave:detail", uuid=leave_request.uuid)


class LeaveRequestDeclineView(ManagerRequiredMixin, View):
    """POST only. URL: /leave/<uuid>/decline/  (name: leave:decline)"""

    def post(self, request, uuid, *args, **kwargs):
        leave_request = get_object_or_404(LeaveRequest, uuid=uuid)
        note = request.POST.get("note", "").strip()
        try:
            services.decline_request(leave_request, declined_by=request.user, note=note)
            messages.warning(
                request, f"Leave request for {leave_request.staff.full_name} has been declined."
            )
        except ValidationError as exc:
            messages.error(request, str(exc))
        return redirect("leave:detail", uuid=leave_request.uuid)
