from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    DeleteView,
)

from payroll.forms import SalaryAssignmentForm
from payroll.mixins import (
    PayrollAuditMixin,
    PayrollContextMixin,
    PayrollDeleteMessageMixin,
    PayrollLoginRequiredMixin,
    PayrollPermissionMixin,
    PayrollSuccessMessageMixin,
)
from payroll.models import SalaryAssignment

from django.db.models import Q


class SalaryAssignmentListView(
    PayrollLoginRequiredMixin,
    PayrollPermissionMixin,
    PayrollContextMixin,
    ListView,
):
    """
    List all staff salary assignments.
    """

    model = SalaryAssignment

    template_name = "payroll/salary_assignment/list.html"

    context_object_name = "assignments"

    paginate_by = 25

    page_title = "Salary Assignments"

    page_heading = "Salary Assignments"

    required_permissions = [
        "payroll.view_salaryassignment",
    ]

    def get_queryset(self):

        queryset = (
            SalaryAssignment.objects
            .select_related(
                "staff",
                "staff__user",
                "salary_structure",
            )
        )

        search = self.request.GET.get("q")

        status = self.request.GET.get("status")

        if search:

            queryset = queryset.filter(
                staff__user__first_name__icontains=search
            ) | queryset.filter(
                staff__user__last_name__icontains=search
            ) | queryset.filter(
                employee_number__icontains=search
            )

        if status == "active":
            queryset = queryset.filter(is_active=True)

        elif status == "inactive":
            queryset = queryset.filter(is_active=False)

        return queryset.order_by(
            "staff__user__last_name",
            "staff__user__first_name",
        )

class SalaryAssignmentCreateView(
    PayrollLoginRequiredMixin,
    PayrollPermissionMixin,
    PayrollContextMixin,
    PayrollSuccessMessageMixin,
    PayrollAuditMixin,
    CreateView,
):

    model = SalaryAssignment

    form_class = SalaryAssignmentForm

    template_name = "payroll/salary_assignment/form.html"

    success_url = reverse_lazy(
        "payroll:salary-assignment-list"
    )

    page_title = "Assign Salary Structure"

    page_heading = "Assign Salary Structure"

    success_message = (
        "Salary Structure assigned successfully."
    )

    required_permissions = [
        "payroll.add_salaryassignment",
    ]

class SalaryAssignmentUpdateView(
    PayrollLoginRequiredMixin,
    PayrollPermissionMixin,
    PayrollContextMixin,
    PayrollSuccessMessageMixin,
    PayrollAuditMixin,
    UpdateView,
):

    model = SalaryAssignment

    form_class = SalaryAssignmentForm

    template_name = "payroll/salary_assignment/form.html"

    success_url = reverse_lazy(
        "payroll:salary-assignment-list"
    )

    page_title = "Update Salary Assignment"

    page_heading = "Update Salary Assignment"

    success_message = (
        "Salary Assignment updated successfully."
    )

    required_permissions = [
        "payroll.change_salaryassignment",
    ]


class SalaryAssignmentDeleteView(
    PayrollLoginRequiredMixin,
    PayrollPermissionMixin,
    PayrollContextMixin,
    PayrollDeleteMessageMixin,
    DeleteView,
):

    model = SalaryAssignment

    template_name = "payroll/salary_assignment/delete.html"

    success_url = reverse_lazy(
        "payroll:salary-assignment-list"
    )

    delete_message = (
        "Salary Assignment deleted successfully."
    )

    required_permissions = [
        "payroll.delete_salaryassignment",
    ]

    def dispatch(self, request, *args, **kwargs):

        assignment = self.get_object()

        if assignment.payrolls.exists():

            messages.error(
                request,
                (
                    "Payroll has already been generated "
                    "using this assignment. "
                    "It cannot be deleted."
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

from django.shortcuts import get_object_or_404, redirect
from django.views import View


class ActivateSalaryAssignmentView(
    PayrollLoginRequiredMixin,
    PayrollPermissionMixin,
    View,
):

    required_permissions = [
        "payroll.change_salaryassignment",
    ]

    def post(self, request, pk):

        assignment = get_object_or_404(
            SalaryAssignment,
            pk=pk,
        )

        SalaryAssignment.objects.filter(
            staff=assignment.staff
        ).update(
            is_active=False
        )

        assignment.is_active = True

        assignment.save(
            update_fields=[
                "is_active",
            ]
        )

        messages.success(
            request,
            "Salary Assignment activated successfully."
        )

        return redirect(
            "payroll:salary-assignment-list"
        )

class DeactivateSalaryAssignmentView(
    PayrollLoginRequiredMixin,
    PayrollPermissionMixin,
    View,
):

    required_permissions = [
        "payroll.change_salaryassignment",
    ]

    def post(self, request, pk):

        assignment = get_object_or_404(
            SalaryAssignment,
            pk=pk,
        )

        assignment.is_active = False

        assignment.save(
            update_fields=[
                "is_active",
            ]
        )

        messages.success(
            request,
            "Salary Assignment deactivated."
        )

        return redirect(
            "payroll:salary-assignment-list"
        )