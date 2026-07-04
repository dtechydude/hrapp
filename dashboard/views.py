from django.shortcuts import render
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


# Create your views here.
@login_required
def landing_page(request):
    return render(request, 'dashboard/hrpams_dashboard.html')

@login_required
def dashboard(request):  
    users_num = User.objects.count()
    # employee_num = Employee.objects.count()
    # employee_num_current = Employee.objects.filter(employee_status__in=['active', 'inactive']).count()
    # num_of_category = Category.objects.count()
   
    # inactive_employee = Employee.objects.filter(employee_status='inactive').count()

    # active = Employee.objects.filter(employee_status='active').count()
    

    # try:
    #     num_indept = Employee.objects.filter(department = request.user.employee.department).count()
    # except Employee.DoesNotExist:
    #     num_indept = Employee.objects.filter()
    # # Build a paginator with function based view
    # queryset = Employee.objects.all().order_by("-id")
    # page = request.GET.get('page', 1)
    # paginator = Paginator(queryset, 40)
    # try:
    #     events = paginator.page(page)
    # except PageNotAnInteger:
    #     events = paginator.page(1)
    # except EmptyPage:
    #     events = paginator.page(paginator.num_pages)
    
    
       
    context = {        
        'users_num' :users_num , 
        # 'employee_num_current' : employee_num_current,
        # 'employee_num_current' : employee_num_current
        

    }
        
    return render(request, 'dashboard/employee_home.html', context )    


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

# Employees Dashboard
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.views.generic import View

from employees.models import Staff

from .services import build_employee_dashboard_context


class DashboardHomeView(LoginRequiredMixin, View):
    """URL: /dashboard/  (name: dashboard:home)"""

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
