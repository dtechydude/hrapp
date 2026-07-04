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
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import  DetailView
import csv
from django.http import HttpResponse
from datetime import date, timedelta
from django.core.mail import send_mass_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import render

from employees.models import Staff
from .services import build_employee_dashboard_context


# Admin Home Page

@login_required
def admin_dashboard(request):
    """
    Root dashboard.

    Staff/Admin users see the management dashboard.
    Employees are redirected to their self-service dashboard.
    """

    # Django administrators / HR / Managers
    if request.user.is_superuser or request.user.is_staff:
        return render(
            request,
            "dashboard/hrpams_dashboard.html",
            {
                "page_title": "Dashboard",
                "breadcrumb": "Dashboard",
            },
        )

    # Normal employee
    return redirect("dashboard:staff-home")

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
        This project already has (or is building, per hrpams_dashboard.html
        in the frontend prototype package) a full management dashboard with
        KPIs, charts, and the complete sidebar. Wire your existing
        admin-dashboard context/queries in here — this stub deliberately
        does not overwrite work already in progress elsewhere.
        """
        return render(
            request,
            "dashboard/employee_home.html",
            {"page_title": "Dashboard", "breadcrumb": "Dashboard"},
        )

    # ── Employee Self-Service dashboard ──────────────────────────────
    def _render_employee_dashboard(self, request):
        try:
            staff = request.user.staff_profile
        except Staff.DoesNotExist:
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



