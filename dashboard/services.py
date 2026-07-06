"""
dashboard/services.py
───────────────────────────────────────────────────────────────────────────
Builds the context payload for the Employee Self-Service dashboard.

Business logic lives here — the view stays a thin orchestrator, per the
project's architecture standard.

Data-source contract
─────────────────────
This service reads from the payroll, leave, and loan apps if they are
installed. Every lookup is guarded so the dashboard degrades gracefully
(shows an empty state) instead of throwing a 500 while those modules are
still being built out elsewhere in the project.

  payroll.Payslip              staff, period, gross_salary,
                                total_deductions, net_salary, status,
                                pay_date
  leave.LeaveRequest            staff, leave_type, start_date, end_date,
                                status
  leave.LeaveBalance            staff, leave_type, entitled_days,
                                used_days
  loan.Loan                     staff, loan_type, amount, balance,
                                monthly_deduction, status
  employees.EmploymentHistory   staff, event_type, old_value, new_value,
                                effective_date, reason

If your actual model/field names differ, adjust the query helpers below —
the view/template contract (the context dict keys) stays the same either
way, so the template never needs to change.
───────────────────────────────────────────────────────────────────────────
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def _safe_import(module_path: str, name: str):
    """Best-effort import — returns None instead of raising if the target
    app/model isn't available yet, so this dashboard never 500s because a
    sibling module hasn't been built out."""
    try:
        module = __import__(module_path, fromlist=[name])
        return getattr(module, name)
    except (ImportError, AttributeError):
        return None


Payslip = _safe_import("payroll.models", "Payslip")
LeaveRequest = _safe_import("leave.models", "LeaveRequest")
LeaveBalance = _safe_import("leave.models", "LeaveBalance")
Loan = _safe_import("loan.models", "Loan")
EmploymentHistory = _safe_import("employees.models", "EmploymentHistory")


def get_recent_payslips(staff, limit: int = 6):
    if Payslip is None:
        return []
    return list(Payslip.objects.filter(payroll__staff=staff).order_by("-generated_at")[:limit])


def get_leave_summary(staff) -> dict:
    if LeaveBalance is None:
        return {"balances": [], "pending_requests": 0}
    balances = list(LeaveBalance.objects.filter(staff=staff).order_by("leave_type"))
    pending = 0
    if LeaveRequest is not None:
        pending = LeaveRequest.objects.filter(staff=staff, status="Pending").count()
    return {"balances": balances, "pending_requests": pending}


def get_active_loans(staff):
    if Loan is None:
        return []
    return list(
        Loan.objects.filter(staff=staff).exclude(status="Closed").order_by("-id")
    )


def get_employment_history(staff, limit: int = 12):
    if EmploymentHistory is None:
        return []
    return list(
        EmploymentHistory.objects.filter(staff=staff)
        .order_by("-effective_date")[:limit]
    )


@dataclass
class EmployeeDashboardContext:
    staff: Any
    deployment: Any = None
    payslips: list = field(default_factory=list)
    latest_payslip: Any = None
    leave_summary: dict = field(default_factory=dict)
    loans: list = field(default_factory=list)
    total_loan_balance: float = 0
    employment_history: list = field(default_factory=list)

    def as_dict(self) -> dict:
        return dict(self.__dict__)


def build_employee_dashboard_context(staff) -> dict:
    """Single entry point the view calls to assemble everything the
    employee dashboard template needs."""
    payslips = get_recent_payslips(staff)
    loans = get_active_loans(staff)

    ctx = EmployeeDashboardContext(
        staff=staff,
        deployment=getattr(staff, "current_deployment", None),
        payslips=payslips,
        latest_payslip=payslips[0] if payslips else None,
        leave_summary=get_leave_summary(staff),
        loans=loans,
        total_loan_balance=sum((getattr(loan, "balance", 0) or 0) for loan in loans),
        employment_history=get_employment_history(staff),
    )
    return ctx.as_dict()


"""
dashboard/services.py

Business logic that powers dashboard widgets, kept out of views.py
so it's independently testable and reusable (e.g. a future "Growth
Report" page can call get_growth_trend() directly).
"""
from calendar import monthrange
from datetime import date

from django.utils import timezone

from employees.models import EmploymentStatus, Staff
from organization.models import Company


def _month_end(base: date, months_back: int) -> date:
    """Last calendar day of the month `months_back` months before base."""
    month = base.month - months_back
    year = base.year
    while month <= 0:
        month += 12
        year -= 1
    return date(year, month, monthrange(year, month)[1])


def get_growth_trend(months: int = 6) -> list[dict]:
    """
    Point-in-time snapshot of active-staff and client-organization
    counts at the end of each of the last `months` calendar months
    (oldest first). Drives the dashboard growth chart.

    Honesty note: staff counts use each staff member's CURRENT
    employment_status, since there's no historical status log yet
    (that's what the Employment History module will provide). So
    this reads as "staff hired on/before that month who are still
    Active today" rather than a true historical snapshot — accurate
    enough for a trend line, but swap this out once Employment
    History tracking exists.
    """
    today = timezone.localdate()
    trend = []

    for i in range(months - 1, -1, -1):
        cutoff = today if i == 0 else _month_end(today, i)

        staff_count = Staff.objects.filter(
            date_employed__lte=cutoff,
            employment_status=EmploymentStatus.ACTIVE,
        ).count()

        org_count = Company.objects.filter(
            created_at__date__lte=cutoff,
            is_active=True,
        ).count()

        trend.append(
            {
                "month": cutoff.strftime("%b"),
                "staff": staff_count,
                "organizations": org_count,
            }
        )

    return trend
