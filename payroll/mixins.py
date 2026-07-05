"""
Reusable mixins for the Payroll application.

These mixins keep the views clean and avoid duplication.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.urls import reverse_lazy


class PayrollLoginRequiredMixin(LoginRequiredMixin):
    """
    Ensures the user is authenticated before accessing payroll pages.
    """

    login_url = reverse_lazy("login")
    redirect_field_name = "next"


class PayrollPermissionMixin:
    """
    Lightweight permission mixin.

    Set `required_permissions` in any view.

    Example:
        required_permissions = [
            "payroll.view_payroll",
            "payroll.generate_payroll",
        ]
    """

    required_permissions = []

    def dispatch(self, request, *args, **kwargs):

        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)

        if self.required_permissions:

            missing = [
                perm
                for perm in self.required_permissions
                if not request.user.has_perm(perm)
            ]

            if missing:
                raise PermissionDenied(
                    "You do not have permission to perform this action."
                )

        return super().dispatch(request, *args, **kwargs)


class PayrollContextMixin:
    """
    Injects common template context into all payroll pages.
    """

    page_title = "Payroll"
    page_icon = "bi-cash-stack"
    page_heading = "Payroll"

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        context.update(
            {
                "page_title": self.page_title,
                "page_heading": self.page_heading,
                "page_icon": self.page_icon,
                "module": "Payroll",
            }
        )

        return context


class PayrollSuccessMessageMixin:
    """
    Displays success messages after form submission.
    """

    success_message = "Operation completed successfully."

    def form_valid(self, form):

        response = super().form_valid(form)

        messages.success(
            self.request,
            self.success_message,
        )

        return response


class PayrollAuditMixin:
    """
    Automatically populates created_by and updated_by
    if those fields exist on the model.
    """

    def form_valid(self, form):

        obj = form.instance

        if hasattr(obj, "created_by") and not obj.pk:
            obj.created_by = self.request.user

        if hasattr(obj, "updated_by"):
            obj.updated_by = self.request.user

        return super().form_valid(form)


class PayrollDeleteMessageMixin:
    """
    Shows a confirmation message after delete.
    """

    delete_message = "Record deleted successfully."

    def delete(self, request, *args, **kwargs):

        response = super().delete(request, *args, **kwargs)

        messages.success(
            request,
            self.delete_message,
        )

        return response