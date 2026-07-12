from __future__ import annotations
from django.shortcuts import render, redirect
import csv
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from users.forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm, StudentEnrollmentForm, TeacherEmploymentUpdateForm, UserTwoUpdateForm, UserRegistrationForm
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.http import JsonResponse
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied

from django.contrib.auth import views as auth_views
from django.db.utils import OperationalError, ProgrammingError


import json
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views import View
from django.utils.decorators import method_decorator

from .forms import BulkPhotoUploadForm
from dashboard.models import CorporateIdentity

# Create your views here.

# Enrollment of new student
def user_registration(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'New user account has been created!' )
            return redirect('/')
    else:
        form = UserRegisterForm()
        user = request.user
        if user.is_superuser or user.is_staff:
            return render(request, 'users/user_registration.html', {'form': form})
       

    
# STUDENTS ENROLLMENT
@login_required
def student_enrollment(request):
    if request.method == 'POST':
        u_form = UserRegisterForm(request.POST)
        p_form = StudentEnrollmentForm(request.POST, request.FILES)

        if u_form.is_valid() and p_form.is_valid():
            # Get the cleaned data from the forms
            user_data = u_form.cleaned_data
            student_data = p_form.cleaned_data

            # Create the Student object, setting first_name and last_name from the user form
            student = Student(
                first_name=user_data.get('first_name'),
                last_name=user_data.get('last_name'),
                **student_data
            )
            student.save()

            messages.success(request, 'Student has been enrolled successfully')
            return redirect('some_success_url')  # Replace with a valid URL name
    else:
        u_form = UserRegisterForm()
        p_form = StudentEnrollmentForm()

    context = {
        'u_form': u_form,
        'p_form': p_form,
    }

    return render(request, 'users/student_enrollment.html', context)


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'New user account has been created!' )
            return redirect('pages:success_submission')
    else:
        form = UserRegisterForm()
        user = request.user
        if user.is_superuser or user.is_staff:
            return render(request, 'users/register.html', {'form': form})
        else:
            return render(request, 'pages/portal_home.html')       
    

# BASIC PROFILE UPDATE
@login_required
def profile_edit(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, f'Your profile has been updated successfully')
            return redirect('pages:success_submission')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        'p_form': p_form,
    }

    return render(request, 'users/profile.html', context)

# BASIC PROFILE UPDATE For Staff
@login_required
def employment_edit(request):
    if request.method == 'POST':
        u_form = UserTwoUpdateForm(request.POST, instance=request.user)
        p_form = TeacherEmploymentUpdateForm(request.POST, request.FILES, instance=request.user.teacher)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, f'Your profile has been updated successfully')
            return redirect('pages:success_submission')
    else:
        u_form = UserTwoUpdateForm(instance=request.user)
        p_form = TeacherEmploymentUpdateForm(instance=request.user.teacher)

    context = {
        'u_form': u_form,
        'p_form': p_form,
    }

    return render(request, 'users/employment_profile.html', context)


 # new user login logic   
def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # Handle 'next' parameter for redirection after login
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('/dashboard/') # Redirect to a default page if no 'next'
    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {'form': form})


def user_logout(request):
    logout(request)
    # Redirect to a new URL. You have a few options:
    
    # Option 1: Redirect to the homepage
    return redirect('logout_success')  # Assumes you have a URL named 'home'


def logout_success(request):
    # return render (request, 'users/logout.html')
    return render (request, 'users/lockscreen.html')



# @login_required
def locked_home(request):
    return render(request, 'users/lockscreen.html')


# all users
@login_required
def all_users(request):
    """
    A view to display all users and export them to a CSV,
    only accessible by staff users.
    """
    user = request.user
    
    # Restrict access to only staff users
    if not user.is_staff:
        return redirect('pages/portal_home.html') # Redirect to a safe URL for non-staff users

    all_users_list = User.objects.all().order_by('last_name', 'first_name')
    
    # Handle CSV export request
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="all_users.csv"'

        writer = csv.writer(response)
        writer.writerow(['Username', 'First Name', 'Last Name', 'Email', 'Phone', 'State Of Origin', 'User Type', 'Registered Date'])

        for u in all_users_list:
            writer.writerow([u.username, u.first_name, u.last_name, u.email, u.profile.phone, u.profile.state_of_origin, u.profile.user_type, u.profile.created])
        return response

    # Normal template rendering
    context = {'all_users': all_users_list,
             'total_count': all_users_list.count()
            }
    return render(request, 'users/all_registered_users.html', context)


@login_required
def enroll_success(request):
    return render(request, 'users/enroll_success.html')


def check_username(request):
    """
    Checks if a username is already taken.
    """
    if request.method == 'GET':
        username = request.GET.get('username', None)
        is_taken = User.objects.filter(username__iexact=username).exists()
        data = {
            'is_taken': is_taken
        }
        return JsonResponse(data)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)



class CustomLoginView(LoginView):
    template_name = 'users/login.html'

    def get_success_url(self):
        # # Check if the logged-in user is associated with a Parent object
        # is_employee = Employee.objects.filter(user=self.request.user).exists()

        # if is_employee:
        #     return reverse_lazy('students:parent-dashboard')
        
        # If not a parent, use the default redirect URL
        return super().get_success_url()
    



class SafePasswordResetView(auth_views.PasswordResetView):
    template_name = 'users/password_reset_form.html'
    email_template_name = 'registration/password_reset_email_text.txt'
    html_email_template_name = 'registration/password_reset_email.html'

    def get_extra_email_context(self):
        context = super().get_extra_email_context() or {}

        try:
            context['corporate_info'] = CorporateIdentity.objects.first()
        except (OperationalError, ProgrammingError):
            # Table does not exist yet (before migration)
            context['corporate_info'] = None

        return context


"""
users/bulk_photo_views.py
───────────────────────────────────────────────────────────────────────────
Independent bulk profile-photo upload views. Kept out of users/views.py
entirely so your existing single-photo admin upload flow is completely
untouched — this file only needs two lines added to users/urls.py to
wire in (see the README).
───────────────────────────────────────────────────────────────────────────
"""
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View

from .services import get_category_choices, get_profiles_for_type, save_bulk_photos

logger = logging.getLogger(__name__)

VALID_CATEGORIES = tuple(value for value, _ in get_category_choices()) + ("all",)


class ManagerRequiredMixin(LoginRequiredMixin):
    """
    Superusers or is_staff only. Deliberately self-contained (doesn't
    import a mixin from another app) so this feature stays independent
    and doesn't create a new cross-app dependency.
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied("You do not have permission to bulk-upload profile photos.")
        return super().dispatch(request, *args, **kwargs)


def _is_manager(user):
    return user.is_active and (user.is_staff or user.is_superuser)


# ── Main view ──────────────────────────────────────────────────────────

class BulkPhotoUploadView(ManagerRequiredMixin, View):
    template_name = "users/bulk_photo_upload.html"

    def _ctx(self):
        return {
            "category_choices": get_category_choices(),
            "page_title": "Bulk Photo Upload",
            "breadcrumb": "Bulk Photo Upload",
        }

    def get(self, request):
        return render(request, self.template_name, self._ctx())

    def post(self, request):
        uploaded_files = {k: request.FILES[k] for k in request.FILES if k.startswith("photo_")}

        if not uploaded_files:
            messages.warning(request, "No photos were selected. Click a card and pick an image first.")
            return render(request, self.template_name, self._ctx())

        results = save_bulk_photos(uploaded_files)

        summary = f"Done — {results['saved']} photo(s) saved, {results['skipped']} skipped."
        level = messages.warning if results["errors"] else messages.success
        level(request, summary)

        ctx = self._ctx()
        ctx.update({"results": results, "summary": summary})
        return render(request, self.template_name, ctx)


# ── AJAX: load user grid ──────────────────────────────────────────────

@login_required
@user_passes_test(_is_manager)
def ajax_load_profiles(request):
    """
    GET ?user_type=employee|<UserType value>|all

    Returns JSON list of profile/staff dicts for the photo grid. URL
    name (see urls.py) is `bulk-photo-load-users`, referenced from the
    fetch call in bulk_photo_upload.html. Query param is still named
    `user_type` to match the existing dropdown id in the template —
    its accepted values now include 'employee' alongside the Profile
    UserType values.
    """
    category = request.GET.get("user_type", "").strip()

    if category not in VALID_CATEGORIES:
        return JsonResponse(
            {"error": f'Invalid category "{category}". Must be one of: {", ".join(VALID_CATEGORIES)}.'},
            status=400,
        )

    try:
        users = get_profiles_for_type(category)
        return JsonResponse({"users": users, "count": len(users)})
    except Exception as e:
        logger.exception("ajax_load_profiles: unhandled exception")
        return JsonResponse({"error": str(e)}, status=500)
