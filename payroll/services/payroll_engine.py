"""
payroll/services/payroll_engine.py

The "Run Payroll" orchestrator — this is what turns a PayrollPeriod
into actual Payroll + PayrollItem records for every staff member
currently deployed to that period's client organization.

Design:
- One staff member's failure (missing salary assignment, bad
  formula, etc.) does not abort the whole run — it's recorded and
  the run continues, so 349 correct payrolls aren't blocked by one
  broken one. See PayrollRun.total_staff/successful/failed.
- Re-running a DRAFT/PROCESSING period is safe and idempotent: each
  staff member's Payroll + PayrollItem rows are fully replaced, not
  duplicated (guarded by the unique_together constraint on Payroll).
  Once a period is APPROVED/PAID/LOCKED it can never be re-run — see
  PayrollPeriod.is_locked-style checks in views.py.
- Variable per-staff inputs (StaffDeduction, StaffAllowance, Bonus,
  Penalty, SalaryAdvance) are layered on top of the base
  SalaryCalculator result rather than requiring HR to re-enter them
  into the salary structure every month — this is the actual "easy
  to manage" mechanism the whole engine exists for.
"""
from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Optional

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum

from employees.models import Staff
from organization.models import StaffDeployment
from payroll.models.advance import SalaryAdvance
from payroll.models.allowance import StaffAllowance
from payroll.models.bonus import Bonus
from payroll.models.choices import ComponentNature, PaymentStatus, PayrollStatus
from payroll.models.deduction import StaffDeduction
from payroll.models.payroll import Payroll
from payroll.models.payroll_item import PayrollItem
from payroll.models.payroll_period import PayrollPeriod
from payroll.models.payroll_run import PayrollRun
from payroll.models.penalty import Penalty

from .salary_calculator import SalaryCalculator

User = get_user_model()


@dataclass
class StaffPayrollFailure:
    staff: Staff
    error: str


@dataclass
class PayrollRunResult:
    run: PayrollRun
    failures: List[StaffPayrollFailure] = field(default_factory=list)


def run_payroll(payroll_period: PayrollPeriod, user: Optional[User] = None) -> PayrollRunResult:
    """
    Generates/regenerates payroll for every staff member currently
    deployed to `payroll_period.company`.

    Raises ValidationError up front if the period is already
    APPROVED/PAID/LOCKED — those must never be silently regenerated.
    """
    if payroll_period.status in (PayrollStatus.APPROVED, PayrollStatus.PAID, PayrollStatus.LOCKED):
        raise ValidationError(
            f"Cannot run payroll for a period that is already {payroll_period.status}."
        )

    deployments = (
        StaffDeployment.objects.current()
        .filter(company=payroll_period.company)
        .select_related("staff")
    )

    last_run_number = (
        PayrollRun.objects.filter(payroll_period=payroll_period)
        .order_by("-run_number")
        .values_list("run_number", flat=True)
        .first()
    )
    run = PayrollRun.objects.create(
        payroll_period=payroll_period,
        run_number=(last_run_number or 0) + 1,
        started_by=user,
        total_staff=deployments.count(),
    )

    failures: List[StaffPayrollFailure] = []
    successful = 0

    for deployment in deployments:
        staff = deployment.staff
        try:
            with transaction.atomic():
                _process_staff_payroll(payroll_period, staff, deployment, user)
            successful += 1
        except ValidationError as exc:
            failures.append(StaffPayrollFailure(staff=staff, error="; ".join(exc.messages)))
        except Exception as exc:  # noqa: BLE001 — one bad row must never kill the run
            failures.append(StaffPayrollFailure(staff=staff, error=str(exc)))

    payroll_period.status = PayrollStatus.PROCESSING
    payroll_period.save(update_fields=["status"])

    run.successful = successful
    run.failed = len(failures)
    run.remarks = "\n".join(f"{f.staff.employee_no}: {f.error}" for f in failures)
    run.complete()

    return PayrollRunResult(run=run, failures=failures)


@transaction.atomic
def _process_staff_payroll(
    payroll_period: PayrollPeriod,
    staff: Staff,
    deployment: StaffDeployment,
    user: Optional[User],
) -> Payroll:
    """
    Calculates and persists one staff member's payroll for this
    period. Replaces any existing (unlocked) Payroll for this
    staff+period combination rather than duplicating it.
    """
    calculation = SalaryCalculator(staff).calculate()

    payroll, _created = Payroll.objects.update_or_create(
        payroll_period=payroll_period,
        staff=staff,
        defaults={
            "salary_assignment": calculation["salary_assignment"],
            "deployment": deployment,
            "processed_by": user,
        },
    )

    # Re-running: wipe previous line items for this payroll before
    # regenerating — the Payroll header itself is reused (its FK
    # relationships like payments/approvals stay intact), only the
    # earnings/deductions breakdown is rebuilt from scratch.
    payroll.items.all().delete()

    for calc_item in calculation["items"]:
        PayrollItem.objects.create(
            payroll=payroll,
            component=calc_item["component"],
            description=calc_item["description"],
            quantity=calc_item["quantity"],
            rate=calc_item["rate"],
        )

    _apply_staff_deductions(payroll, staff, payroll_period)
    _apply_staff_allowances(payroll, staff, payroll_period)
    _apply_bonuses(payroll, staff, payroll_period)
    _apply_penalties(payroll, staff, payroll_period)
    _apply_salary_advances(payroll, staff, payroll_period)

    _recalculate_payroll_totals(payroll)

    return payroll


def _apply_staff_deductions(payroll: Payroll, staff: Staff, period: PayrollPeriod) -> None:
    for deduction in StaffDeduction.objects.filter(staff=staff, is_active=True).select_related("component"):
        if not deduction.is_due_for(period.payroll_date):
            continue
        PayrollItem.objects.create(
            payroll=payroll,
            component=deduction.component,
            description=deduction.reason or deduction.component.name,
            quantity=Decimal("1.00"),
            rate=deduction.amount,
        )
        deduction.mark_applied(period)


def _apply_staff_allowances(payroll: Payroll, staff: Staff, period: PayrollPeriod) -> None:
    for allowance in StaffAllowance.objects.filter(staff=staff, is_active=True).select_related("component"):
        if not allowance.is_due_for(period.payroll_date):
            continue
        PayrollItem.objects.create(
            payroll=payroll,
            component=allowance.component,
            description=allowance.reason or allowance.component.name,
            quantity=Decimal("1.00"),
            rate=allowance.amount,
        )
        allowance.mark_applied(period)


def _apply_bonuses(payroll: Payroll, staff: Staff, period: PayrollPeriod) -> None:
    bonuses = Bonus.objects.filter(staff=staff, target_period=period).select_related("component")
    for bonus in bonuses:
        if not bonus.is_due:
            continue
        PayrollItem.objects.create(
            payroll=payroll,
            component=bonus.component,
            description=bonus.reason,
            quantity=Decimal("1.00"),
            rate=bonus.amount,
        )
        bonus.mark_applied(period)


def _apply_penalties(payroll: Payroll, staff: Staff, period: PayrollPeriod) -> None:
    penalties = Penalty.objects.filter(staff=staff, target_period=period).select_related("component")
    for penalty in penalties:
        if not penalty.is_due:
            continue
        PayrollItem.objects.create(
            payroll=payroll,
            component=penalty.component,
            description=penalty.reason,
            quantity=Decimal("1.00"),
            rate=penalty.amount,
        )
        penalty.mark_applied(period)


def _apply_salary_advances(payroll: Payroll, staff: Staff, period: PayrollPeriod) -> None:
    advances = SalaryAdvance.objects.filter(staff=staff).select_related("component")
    for advance in advances:
        if not advance.is_active_advance:
            continue
        deduction_amount = advance.next_deduction_amount()
        if deduction_amount <= 0:
            continue
        PayrollItem.objects.create(
            payroll=payroll,
            component=advance.component,
            description=f"Salary advance repayment ({advance.reason or 'advance'})",
            quantity=Decimal("1.00"),
            rate=deduction_amount,
        )
        # Needs payroll.pk, which update_or_create already guarantees.
        advance.record_repayment(deduction_amount, payroll)


def _recalculate_payroll_totals(payroll: Payroll) -> None:
    """
    Single source of truth for the Payroll header totals: derived
    from the actual PayrollItem rows just created, not re-computed in
    parallel Python arithmetic that could drift out of sync.
    """
    items = payroll.items.all()

    earnings = items.filter(nature=ComponentNature.EARNING).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    deductions = items.filter(nature=ComponentNature.DEDUCTION).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    taxable = items.filter(nature=ComponentNature.EARNING, is_taxable=True).aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0.00")

    payroll.gross_salary = earnings
    payroll.total_earnings = earnings
    payroll.total_deductions = deductions
    payroll.taxable_income = taxable
    payroll.net_salary = earnings - deductions
    payroll.payment_status = PaymentStatus.PENDING
    payroll.save(
        update_fields=[
            "gross_salary", "total_earnings", "total_deductions",
            "taxable_income", "net_salary", "payment_status", "updated_at",
        ]
    )
