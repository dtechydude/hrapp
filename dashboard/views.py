# from django.views.generic import View
# from django.shortcuts import render, redirect
# from django.core.mail import send_mail
# from django.contrib import messages
# from django.contrib.auth.decorators import login_required
# from django.db.models import Count
# from django.contrib.auth.models import User
# from users.models import Profile
# from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
# from django.core.exceptions import ObjectDoesNotExist
# from django.contrib.auth.mixins import LoginRequiredMixin
# from django.views.generic import  DetailView
# import csv
# from django.http import HttpResponse
# from datetime import date, timedelta
# from django.core.mail import send_mass_mail, EmailMultiAlternatives
# from django.template.loader import render_to_string
# from django.utils.html import strip_tags

# from django.contrib.auth.mixins import LoginRequiredMixin
# from django.core.exceptions import PermissionDenied
# from django.shortcuts import render

# from employees.models import Staff
# from .services import build_employee_dashboard_context


# # Admin Home Page

# @login_required
# def admin_dashboard(request):
#     """
#     Root dashboard.

#     Staff/Admin users see the management dashboard.
#     Employees are redirected to their self-service dashboard.
#     """

#     # Django administrators / HR / Managers
#     if request.user.is_superuser or request.user.is_staff:
#         return render(
#             request,
#             "dashboard/hrpams_dashboard.html",
#             {
#                 "page_title": "Dashboard",
#                 "breadcrumb": "Dashboard",
#             },
#         )

#     # Normal employee
#     return redirect("dashboard:staff-home")


# from datetime import timedelta

# from django.contrib.auth.mixins import LoginRequiredMixin
# from django.utils import timezone
# from django.views.generic import TemplateView

# from employees.models import EmploymentStatus, Staff
# from organization.models import Company, StaffDeployment

# from .services import get_growth_trend


# class DashboardView(LoginRequiredMixin, TemplateView):
#     """
#     HRPAMS landing page.

#     KPI cards and the growth chart are backed by live queries below.
#     Payroll, loan, and attendance figures are intentionally NOT set
#     here — those modules don't exist yet, and the template's own
#     `|default:"..."` fallbacks handle that gracefully. Once payroll
#     ships, add its context here rather than hardcoding numbers in
#     the template.
#     """

#     template_name = "dashboard/hrpams_dashboard.html"

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)

#         today = timezone.localdate()
#         month_start = today.replace(day=1)
#         last_month_start = (month_start - timedelta(days=1)).replace(day=1)

#         # ── Staff ──
#         total_active_staff = Staff.objects.filter(
#             employment_status=EmploymentStatus.ACTIVE
#         ).count()

#         new_hires_this_month = Staff.objects.filter(date_employed__gte=month_start).count()
#         new_hires_last_month = Staff.objects.filter(
#             date_employed__gte=last_month_start, date_employed__lt=month_start
#         ).count()
#         hires_delta = new_hires_this_month - new_hires_last_month

#         suspended_staff = Staff.objects.filter(
#             employment_status=EmploymentStatus.SUSPENDED
#         ).count()
#         staff_on_leave = Staff.objects.filter(
#             employment_status=EmploymentStatus.ON_LEAVE
#         ).count()

#         # ── Organizations ──
#         total_organizations = Company.objects.filter(is_active=True).count()
#         new_organizations_this_month = Company.objects.filter(
#             created_at__date__gte=month_start, is_active=True
#         ).count()

#         # ── Deployment ──
#         deployed_staff_ids = StaffDeployment.objects.current().values_list("staff_id", flat=True)
#         unassigned_staff = (
#             Staff.objects.filter(employment_status=EmploymentStatus.ACTIVE)
#             .exclude(id__in=deployed_staff_ids)
#             .count()
#         )

#         # ── Growth chart ──
#         growth_trend = get_growth_trend(months=6)

#         context.update(
#             {
#                 "total_active_staff": total_active_staff,
#                 "active_staff_trend": f"+{new_hires_this_month}" if new_hires_this_month else "0",

#                 "total_organizations": total_organizations,
#                 "new_organizations_this_month": new_organizations_this_month,
#                 "new_organizations_trend": (
#                     f"+{new_organizations_this_month}" if new_organizations_this_month else "0"
#                 ),

#                 "suspended_staff": suspended_staff,
#                 "staff_on_leave": staff_on_leave,

#                 "new_hires_this_month": new_hires_this_month,
#                 "new_hires_trend": f"{hires_delta:+d}",

#                 "unassigned_staff": unassigned_staff,
#                 "current_month_short": today.strftime("%b"),

#                 "growth_chart_data": {
#                     "labels": [p["month"] for p in growth_trend],
#                     "staff": [p["staff"] for p in growth_trend],
#                     "organizations": [p["organizations"] for p in growth_trend],
#                 },
#             }
#         )
#         return context

# # Employees Dashboard
# class DashboardHomeView(LoginRequiredMixin, View):
#     """URL: /dashboard/  (name: dashboard:staff-home)"""

#     def get(self, request, *args, **kwargs):
#         if request.user.is_superuser or request.user.is_staff:
#             return self._render_admin_dashboard(request)
#         return self._render_employee_dashboard(request)

#     # ── Manager / Admin dashboard ────────────────────────────────────
#     def _render_admin_dashboard(self, request):
#         """
#         This project already has (or is building, per hrpams_dashboard.html
#         in the frontend prototype package) a full management dashboard with
#         KPIs, charts, and the complete sidebar. Wire your existing
#         admin-dashboard context/queries in here — this stub deliberately
#         does not overwrite work already in progress elsewhere.
#         """
#         return render(
#             request,
#             "dashboard/employee_home.html",
#             {"page_title": "Dashboard", "breadcrumb": "Dashboard"},
#         )

#     # ── Employee Self-Service dashboard ──────────────────────────────
#     def _render_employee_dashboard(self, request):
#         try:
#             staff = request.user.staff_profile
#         except Staff.DoesNotExist:
#             raise PermissionDenied(
#                 "Your account is not linked to a staff profile. "
#                 "Please contact HR to have your access configured."
#             )

#         ctx = build_employee_dashboard_context(staff)
#         ctx.update(
#             {
#                 "page_title": "My Dashboard",
#                 "page_subtitle": f"Welcome back, {staff.user.first_name}.",
#                 "breadcrumb": "My Dashboard",
#             }
#         )
#         return render(request, "dashboard/employee_home.html", ctx)
from django.views.generic import View
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.contrib.auth.models import User
from users.models import Profile
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import DetailView
import csv
from django.http import HttpResponse
from datetime import date, timedelta
from django.core.mail import send_mass_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.views.generic import TemplateView

from employees.models import EmploymentStatus, Staff
from organization.models import Company, StaffDeployment

from .services import build_employee_dashboard_context, get_growth_trend


# Admin Home Page Root Router
@login_required
def admin_dashboard(request):
    """
    Root dashboard.

    Staff/Admin users see the management dashboard.
    Employees are redirected to their self-service dashboard.
    """

    # Django administrators / HR / Managers
    if request.user.is_superuser or request.user.is_staff:
        return redirect("dashboard:admin-home")

    # Normal employee
    return redirect("dashboard:staff-home")


class DashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    HRPAMS landing page.

    KPI cards and the growth chart are backed by live queries below.
    Payroll, loan, and attendance figures are intentionally NOT set
    here — those modules don't exist yet, and the template's own
    `|default:"..."` fallbacks handle that gracefully. Once payroll
    ships, add its context here rather than hardcoding numbers in
    the template.
    """

    template_name = "dashboard/hrpams_dashboard.html"

    def test_func(self):
        """Restrict access to superusers and staff members only."""
        return self.request.user.is_superuser or self.request.user.is_staff

    def handle_no_permission(self):
        """Redirect employees trying to access this URL back to their staff dashboard."""
        if self.request.user.is_authenticated:
            return redirect("dashboard:staff-home")
        return super().handle_no_permission()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        today = timezone.localdate()
        month_start = today.replace(day=1)
        last_month_start = (month_start - timedelta(days=1)).replace(day=1)

        # ── Staff ──
        total_active_staff = Staff.objects.filter(
            employment_status=EmploymentStatus.ACTIVE
        ).count()

        new_hires_this_month = Staff.objects.filter(date_employed__gte=month_start).count()
        new_hires_last_month = Staff.objects.filter(
            date_employed__gte=last_month_start, date_employed__lt=month_start
        ).count()
        hires_delta = new_hires_this_month - new_hires_last_month

        suspended_staff = Staff.objects.filter(
            employment_status=EmploymentStatus.SUSPENDED
        ).count()
        staff_on_leave = Staff.objects.filter(
            employment_status=EmploymentStatus.ON_LEAVE
        ).count()

        # ── Organizations ──
        total_organizations = Company.objects.filter(is_active=True).count()
        new_organizations_this_month = Company.objects.filter(
            created_at__date__gte=month_start, is_active=True
        ).count()

        # ── Deployment ──
        deployed_staff_ids = StaffDeployment.objects.current().values_list("staff_id", flat=True)
        unassigned_staff = (
            Staff.objects.filter(employment_status=EmploymentStatus.ACTIVE)
            .exclude(id__in=deployed_staff_ids)
            .count()
        )

        # ── Growth chart ──
        growth_trend = get_growth_trend(months=6)

        context.update(
            {
                "total_active_staff": total_active_staff,
                "active_staff_trend": f"+{new_hires_this_month}" if new_hires_this_month else "0",

                "total_organizations": total_organizations,
                "new_organizations_this_month": new_organizations_this_month,
                "new_organizations_trend": (
                    f"+{new_organizations_this_month}" if new_organizations_this_month else "0"
                ),

                "suspended_staff": suspended_staff,
                "staff_on_leave": staff_on_leave,

                "new_hires_this_month": new_hires_this_month,
                "new_hires_trend": f"{hires_delta:+d}",

                "unassigned_staff": unassigned_staff,
                "current_month_short": today.strftime("%b"),

                "growth_chart_data": {
                    "labels": [p["month"] for p in growth_trend],
                    "staff": [p["staff"] for p in growth_trend],
                    "organizations": [p["organizations"] for p in growth_trend],
                },
            }
        )
        return context


# Employees Dashboard
class DashboardHomeView(LoginRequiredMixin, View):
    """URL: /dashboard/  (name: dashboard:staff-home)"""

    def get(self, request, *args, **kwargs):
        if request.user.is_superuser or request.user.is_staff:
            return self._render_admin_dashboard(request)
        return self._render_employee_dashboard(request)

    # ── Manager / Admin dashboard ────────────────────────────────────
    def _render_admin_dashboard(self, request):
        """
        Redirect to the dedicated Management Dashboard view class instead of
        rendering the employee home with missing parameters.
        """
        return redirect("dashboard:admin-home")

    # ── Employee Self-Service dashboard ──────────────────────────────
    def _render_employee_dashboard(self, request):
        try:
            staff = request.user.staff_profile
        except ObjectDoesNotExist:
            raise PermissionDenied(
                "Your account is not linked to a staff profile. "
                "Please contact HR to have your access configured."
            )

        ctx = build_employee_dashboard_context(staff)
        ctx.update(
            {
                "page_title": "My Dashboard",
                "page_subtitle": f"Welcome back, {staff.user.first_name}.",
                "breadcrumb": "My Dashboard",
            }
        )
        return render(request, "dashboard/employee_home.html", ctx)

    
# Other Pages

@login_required        
def help_center(request):
    return render(request, 'dashboard/help_center.html')

@login_required
def support_info(request):
    return render(request, 'dashboard/support_info.html',)

@login_required
def lock_screen(request):
    return render(request, 'dashboard/lockscreen.html')

@login_required
def success_submission(request):
    return render(request, 'dashboard/success_submission.html')



