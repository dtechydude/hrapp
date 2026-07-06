"""
payroll/services/employee_dashboard.py

A small bridge for the existing employee dashboard view (wherever it
lives — not part of this app) to pull real payslip data without
needing to know Payroll's internal field names.

Usage in your EmployeeDashboardView:

    from payroll.services.employee_dashboard import get_employee_payroll_dashboard_context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_employee_payroll_dashboard_context(self.request.user.staff))
        return context

Relies on Payroll.period / Payroll.status (see models/payroll.py) —
convenience aliases for payroll_period.period_name / payment_status —
so employee_home.html's existing `{{ p.period }}` / `{{ p.status }}`
references work without any template changes.
"""
from payroll.models.payroll import Payroll


def get_employee_payroll_dashboard_context(staff, recent_count: int = 5) -> dict:
    payrolls = (
        Payroll.objects.filter(staff=staff)
        .select_related("payroll_period", "payroll_period__company")
        .order_by("-payroll_period__year", "-payroll_period__month")
    )
    return {
        "payslips": list(payrolls[:recent_count]),
        "latest_payslip": payrolls.first(),
    }
