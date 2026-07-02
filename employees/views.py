from django.db import transaction
from django.views.generic import CreateView, ListView, DetailView
from django.urls import reverse_lazy
from django.shortcuts import redirect
from .forms import StaffUserForm, StaffProfileForm
from .models import Staff
from .mixins import StaffManagerRequiredMixin

class StaffCreateView(StaffManagerRequiredMixin, CreateView):
    model = Staff
    template_name = 'employees/staff_form.html'
    form_class = StaffProfileForm
    success_url = reverse_lazy('employees:add')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['user_form'] = StaffUserForm(self.request.POST)
        else:
            context['user_form'] = StaffUserForm()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        user_form = context['user_form']
        with transaction.atomic():
            if user_form.is_valid():
                user = user_form.save(commit=False)
                user.set_password("DefaultPassword123!") # Default policy
                user.save()
                staff = form.save(commit=False)
                staff.user = user
                staff.created_by = self.request.user
                staff.save()
                return redirect(self.success_url)
        return self.render_to_response(self.get_context_data(form=form))

from django.db import transaction
from django.views.generic import CreateView, UpdateView, ListView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from .forms import StaffUserForm, StaffProfileForm
from .models import Staff
from .mixins import StaffManagerRequiredMixin

class StaffListView(StaffManagerRequiredMixin, ListView):
    model = Staff
    template_name = 'employees/staff_list.html'
    context_object_name = 'staff_list'
    paginate_by = 20

    def get_queryset(self):
        # Optimized query to prevent N+1 issues with the User model
        return Staff.objects.select_related('user', 'staff_rank').filter(is_active=True)

class StaffUpdateView(StaffManagerRequiredMixin, UpdateView):
    model = Staff
    template_name = 'employees/staff_form.html'
    form_class = StaffProfileForm
    success_url = reverse_lazy('employees:list')

    # Add these two lines to fix the lookup
    slug_field = 'uuid'          # The name of the field in your model
    slug_url_kwarg = 'uuid'      # The name of the parameter in your urls.py

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['user_form'] = StaffUserForm(self.request.POST, instance=self.object.user)
        else:
            context['user_form'] = StaffUserForm(instance=self.object.user)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        user_form = context['user_form']
        with transaction.atomic():
            if user_form.is_valid():
                user_form.save()
                return super().form_valid(form)
        return self.render_to_response(self.get_context_data(form=form))