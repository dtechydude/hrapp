from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    DetailView,
)

from payroll.forms import PayrollPeriodForm
from payroll.models import PayrollPeriod
from payroll.services.payroll_generator import PayrollGenerator

from payroll.mixins import (
    PayrollLoginRequiredMixin,
    PayrollPermissionMixin,
    PayrollContextMixin,
    PayrollSuccessMessageMixin,
    PayrollAuditMixin,
)

class PayrollPeriodListView(
    PayrollLoginRequiredMixin,
    PayrollPermissionMixin,
    PayrollContextMixin,
    ListView,
):

    model = PayrollPeriod

    template_name = "payroll/payroll_period/list.html"

    context_object_name = "periods"

    paginate_by = 20

    page_title = "Payroll Periods"
    page_heading = "Payroll Periods"

    required_permissions = [
        "payroll.view_payrollperiod",
    ]

    def get_queryset(self):

        return (
            PayrollPeriod.objects
            .select_related("company")
            .order_by("-year", "-month")
        )


class PayrollPeriodCreateView(
    PayrollLoginRequiredMixin,
    PayrollPermissionMixin,
    PayrollContextMixin,
    PayrollSuccessMessageMixin,
    PayrollAuditMixin,
    CreateView,
):

    model = PayrollPeriod

    form_class = PayrollPeriodForm

    template_name = "payroll/payroll_period/form.html"

    success_url = reverse_lazy("payroll:period-list")

    page_title = "Create Payroll Period"

    page_heading = "Create Payroll Period"

    success_message = "Payroll Period created successfully."

    required_permissions = [
        "payroll.add_payrollperiod",
    ]


class PayrollPeriodUpdateView(
    PayrollLoginRequiredMixin,
    PayrollPermissionMixin,
    PayrollContextMixin,
    PayrollSuccessMessageMixin,
    PayrollAuditMixin,
    UpdateView,
):

    model = PayrollPeriod

    form_class = PayrollPeriodForm

    template_name = "payroll/payroll_period/form.html"

    success_url = reverse_lazy("payroll:period-list")

    page_title = "Update Payroll Period"

    page_heading = "Update Payroll Period"

    success_message = "Payroll Period updated successfully."

    required_permissions = [
        "payroll.change_payrollperiod",
    ]

    def dispatch(self, request, *args, **kwargs):

        period = self.get_object()

        if period.locked:

            messages.error(
                request,
                "Locked Payroll Period cannot be edited."
            )

            return redirect("payroll:period-detail", pk=period.pk)

        return super().dispatch(request, *args, **kwargs)


class PayrollPeriodDetailView(
    PayrollLoginRequiredMixin,
    PayrollPermissionMixin,
    PayrollContextMixin,
    DetailView,
):

    model = PayrollPeriod

    template_name = "payroll/payroll_period/detail.html"

    context_object_name = "period"

    page_title = "Payroll Period"

    page_heading = "Payroll Period"

    required_permissions = [
        "payroll.view_payrollperiod",
    ]

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        period = self.object

        payrolls = (
            period.payrolls
            .select_related(
                "staff",
                "staff__user",
            )
        )

        context["payrolls"] = payrolls

        context["total_staff"] = payrolls.count()

        context["total_net_salary"] = sum(
            payroll.net_salary
            for payroll in payrolls
        )

        return context


class GeneratePayrollView(
    PayrollLoginRequiredMixin,
    PayrollPermissionMixin,
    View,
):

    required_permissions = [
        "payroll.generate_payroll",
    ]

    def post(self, request, pk):

        period = get_object_or_404(
            PayrollPeriod,
            pk=pk,
        )

        try:

            generator = PayrollGenerator(
                payroll_period=period,
                processed_by=request.user,
            )

            result = generator.generate()

            messages.success(
                request,
                (
                    f"Payroll Generated Successfully."
                    f" Generated: {result['generated']} | "
                    f"Failed: {result['failed']}"
                ),
            )

        except Exception as e:

            messages.error(
                request,
                str(e),
            )

        return redirect(
            "payroll:period-detail",
            pk=pk,
        )


class LockPayrollPeriodView(
    PayrollLoginRequiredMixin,
    PayrollPermissionMixin,
    View,
):

    required_permissions = [
        "payroll.lock_payroll",
    ]

    def post(self, request, pk):

        period = get_object_or_404(
            PayrollPeriod,
            pk=pk,
        )

        if period.locked:

            messages.warning(
                request,
                "Payroll Period is already locked."
            )

        else:

            period.locked = True

            period.save(
                update_fields=[
                    "locked",
                ]
            )

            messages.success(
                request,
                "Payroll Period locked successfully."
            )

        return redirect(
            "payroll:period-detail",
            pk=pk,
        )


class UnlockPayrollPeriodView(
    PayrollLoginRequiredMixin,
    PayrollPermissionMixin,
    View,
):

    required_permissions = [
        "payroll.unlock_payroll",
    ]

    def post(self, request, pk):

        period = get_object_or_404(
            PayrollPeriod,
            pk=pk,
        )

        period.locked = False

        period.save(update_fields=["locked"])

        messages.success(
            request,
            "Payroll Period unlocked successfully."
        )

        return redirect(
            "payroll:period-detail",
            pk=pk,
        )