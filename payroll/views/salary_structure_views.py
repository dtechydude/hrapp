from django.contrib import messages
from django.db import transaction
from django.urls import reverse_lazy
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    DeleteView,
)

from payroll.forms import (
    SalaryStructureForm,
    SalaryStructureItemFormSet,
)

from payroll.mixins import (
    PayrollAuditMixin,
    PayrollContextMixin,
    PayrollDeleteMessageMixin,
    PayrollLoginRequiredMixin,
    PayrollPermissionMixin,
    PayrollSuccessMessageMixin,
)

from payroll.models import SalaryStructure


class SalaryStructureListView(
    PayrollLoginRequiredMixin,
    PayrollPermissionMixin,
    PayrollContextMixin,
    ListView,
):
    """
    List all salary structures.
    """

    model = SalaryStructure

    template_name = "payroll/salary_structure/list.html"

    context_object_name = "structures"

    paginate_by = 20

    page_title = "Salary Structures"

    page_heading = "Salary Structures"

    required_permissions = [
        "payroll.view_salarystructure",
    ]

    def get_queryset(self):

        queryset = SalaryStructure.objects.prefetch_related(
            "items",
            "items__component",
        )

        search = self.request.GET.get("q")

        if search:
            queryset = queryset.filter(
                name__icontains=search
            )

        return queryset.order_by("name")


class SalaryStructureCreateView(
    PayrollLoginRequiredMixin,
    PayrollPermissionMixin,
    PayrollContextMixin,
    PayrollSuccessMessageMixin,
    PayrollAuditMixin,
    CreateView,
):
    """
    Create Salary Structure with inline items.
    """

    model = SalaryStructure

    form_class = SalaryStructureForm

    template_name = "payroll/salary_structure/form.html"

    success_url = reverse_lazy(
        "payroll:salary-structure-list"
    )

    page_title = "Create Salary Structure"

    page_heading = "Create Salary Structure"

    success_message = (
        "Salary Structure created successfully."
    )

    required_permissions = [
        "payroll.add_salarystructure",
    ]

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        if self.request.POST:
            context["formset"] = SalaryStructureItemFormSet(
                self.request.POST
            )
        else:
            context["formset"] = SalaryStructureItemFormSet()

        return context

    @transaction.atomic
    def form_valid(self, form):

        context = self.get_context_data()

        formset = context["formset"]

        if formset.is_valid():

            self.object = form.save()

            formset.instance = self.object

            formset.save()

            messages.success(
                self.request,
                self.success_message,
            )

            return super().form_valid(form)

        return self.form_invalid(form)


class SalaryStructureUpdateView(
    PayrollLoginRequiredMixin,
    PayrollPermissionMixin,
    PayrollContextMixin,
    PayrollSuccessMessageMixin,
    PayrollAuditMixin,
    UpdateView,
):
    """
    Update Salary Structure and its items.
    """

    model = SalaryStructure

    form_class = SalaryStructureForm

    template_name = "payroll/salary_structure/form.html"

    success_url = reverse_lazy(
        "payroll:salary-structure-list"
    )

    page_title = "Update Salary Structure"

    page_heading = "Update Salary Structure"

    success_message = (
        "Salary Structure updated successfully."
    )

    required_permissions = [
        "payroll.change_salarystructure",
    ]

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        if self.request.POST:

            context["formset"] = SalaryStructureItemFormSet(
                self.request.POST,
                instance=self.object,
            )

        else:

            context["formset"] = SalaryStructureItemFormSet(
                instance=self.object,
            )

        return context

    @transaction.atomic
    def form_valid(self, form):

        context = self.get_context_data()

        formset = context["formset"]

        if formset.is_valid():

            self.object = form.save()

            formset.instance = self.object

            formset.save()

            messages.success(
                self.request,
                self.success_message,
            )

            return super().form_valid(form)

        return self.form_invalid(form)


class SalaryStructureDeleteView(
    PayrollLoginRequiredMixin,
    PayrollPermissionMixin,
    PayrollContextMixin,
    PayrollDeleteMessageMixin,
    DeleteView,
):
    """
    Delete Salary Structure.
    """

    model = SalaryStructure

    template_name = "payroll/salary_structure/delete.html"

    success_url = reverse_lazy(
        "payroll:salary-structure-list"
    )

    delete_message = (
        "Salary Structure deleted successfully."
    )

    required_permissions = [
        "payroll.delete_salarystructure",
    ]

    def dispatch(self, request, *args, **kwargs):

        structure = self.get_object()

        if structure.assignments.filter(
            is_active=True
        ).exists():

            messages.error(
                request,
                (
                    "This Salary Structure is assigned to "
                    "active staff and cannot be deleted."
                ),
            )

            return super().get(
                request,
                *args,
                **kwargs,
            )

        return super().dispatch(
            request,
            *args,
            **kwargs,
        )