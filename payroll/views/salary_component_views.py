from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    DeleteView,
)

from payroll.forms import SalaryComponentForm
from payroll.mixins import (
    PayrollAuditMixin,
    PayrollContextMixin,
    PayrollDeleteMessageMixin,
    PayrollLoginRequiredMixin,
    PayrollPermissionMixin,
    PayrollSuccessMessageMixin,
)
from payroll.models import SalaryComponent


class SalaryComponentListView(
    PayrollLoginRequiredMixin,
    PayrollPermissionMixin,
    PayrollContextMixin,
    ListView,
):
    """
    List all salary components.
    """

    model = SalaryComponent

    template_name = "payroll/salary_component/list.html"

    context_object_name = "components"

    paginate_by = 25

    page_title = "Salary Components"

    page_heading = "Salary Components"

    required_permissions = [
        "payroll.view_salarycomponent",
    ]

    def get_queryset(self):

        queryset = SalaryComponent.objects.all()

        search = self.request.GET.get("q")

        component_type = self.request.GET.get("type")

        active = self.request.GET.get("active")

        if search:
            queryset = queryset.filter(
                name__icontains=search
            )

        if component_type:
            queryset = queryset.filter(
                component_type=component_type
            )

        if active == "1":
            queryset = queryset.filter(
                is_active=True
            )

        elif active == "0":
            queryset = queryset.filter(
                is_active=False
            )

        return queryset.order_by(
            "display_order",
            "name",
        )


class SalaryComponentCreateView(
    PayrollLoginRequiredMixin,
    PayrollPermissionMixin,
    PayrollContextMixin,
    PayrollSuccessMessageMixin,
    PayrollAuditMixin,
    CreateView,
):
    """
    Create Salary Component.
    """

    model = SalaryComponent

    form_class = SalaryComponentForm

    template_name = "payroll/salary_component/form.html"

    success_url = reverse_lazy(
        "payroll:salary-component-list"
    )

    page_title = "Create Salary Component"

    page_heading = "Create Salary Component"

    success_message = (
        "Salary Component created successfully."
    )

    required_permissions = [
        "payroll.add_salarycomponent",
    ]


class SalaryComponentUpdateView(
    PayrollLoginRequiredMixin,
    PayrollPermissionMixin,
    PayrollContextMixin,
    PayrollSuccessMessageMixin,
    PayrollAuditMixin,
    UpdateView,
):
    """
    Update Salary Component.
    """

    model = SalaryComponent

    form_class = SalaryComponentForm

    template_name = "payroll/salary_component/form.html"

    success_url = reverse_lazy(
        "payroll:salary-component-list"
    )

    page_title = "Update Salary Component"

    page_heading = "Update Salary Component"

    success_message = (
        "Salary Component updated successfully."
    )

    required_permissions = [
        "payroll.change_salarycomponent",
    ]

    def dispatch(self, request, *args, **kwargs):

        component = self.get_object()

        if component.is_system:

            messages.error(
                request,
                "System Components cannot be modified."
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


class SalaryComponentDeleteView(
    PayrollLoginRequiredMixin,
    PayrollPermissionMixin,
    PayrollContextMixin,
    PayrollDeleteMessageMixin,
    DeleteView,
):
    """
    Delete Salary Component.
    """

    model = SalaryComponent

    template_name = "payroll/salary_component/delete.html"

    success_url = reverse_lazy(
        "payroll:salary-component-list"
    )

    delete_message = (
        "Salary Component deleted successfully."
    )

    required_permissions = [
        "payroll.delete_salarycomponent",
    ]

    def dispatch(self, request, *args, **kwargs):

        component = self.get_object()

        if component.is_system:

            messages.error(
                request,
                "System Components cannot be deleted."
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