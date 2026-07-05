from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from employees.models import Staff

from payroll.models import (
    Payroll,
    PayrollItem,
    PayrollJournal,
    PayrollPayment,
    Payslip,
    SalaryAssignment,
)

from payroll.services.salary_calculator import SalaryCalculator


class PayrollGenerator:
    """
    Enterprise Payroll Generator

    Responsibilities
    ----------------
    • Generate payroll for a payroll period
    • Create Payroll
    • Create Payroll Items
    • Create Payment Record
    • Create Journal
    • Generate Payslip
    • Update Payroll Period totals

    This service is intended to be called only once
    for each Payroll Period.
    """

    def __init__(self, payroll_period, processed_by):

        self.period = payroll_period
        self.user = processed_by

        self.generated = 0
        self.failed = 0
        self.skipped = 0

        self.errors = []

    @transaction.atomic
    def generate(self):

        if self.period.locked:
            raise ValidationError(
                "This payroll period has already been locked."
            )

        if self.period.is_generated:
            raise ValidationError(
                "Payroll has already been generated."
            )

        staffs = (
            Staff.objects.filter(
                is_active=True,
                employment_status="Active",
            )
            .select_related("user")
        )

        for staff in staffs:

            try:

                # Prevent duplicate payroll generation
                if Payroll.objects.filter(
                    payroll_period=self.period,
                    staff=staff,
                ).exists():

                    self.skipped += 1
                    continue

                self.generate_staff_payroll(staff)

                self.generated += 1

            except Exception as exc:

                self.failed += 1

                self.errors.append(
                    f"{staff.full_name}: {exc}"
                )

        # Update Payroll Period statistics
        self.period.is_generated = True
        self.period.generated_at = timezone.now()

        self.period.total_staff = Payroll.objects.filter(
            payroll_period=self.period
        ).count()

        self.period.total_amount = (
            Payroll.objects.filter(
                payroll_period=self.period
            ).aggregate(
                total=Sum("net_salary")
            )["total"]
            or Decimal("0.00")
        )

        self.period.save(
            update_fields=[
                "is_generated",
                "generated_at",
                "total_staff",
                "total_amount",
            ]
        )

        return {
            "generated": self.generated,
            "failed": self.failed,
            "skipped": self.skipped,
            "errors": self.errors,
        }

    def generate_staff_payroll(self, staff):

        assignment = (
            SalaryAssignment.objects
            .select_related("salary_structure")
            .filter(
                staff=staff,
                is_active=True,
            )
            .first()
        )

        if assignment is None:
            raise ValidationError(
                "No active Salary Assignment."
            )

        deployment = staff.current_deployment

        if deployment is None:
            raise ValidationError(
                "Employee has no active deployment."
            )

        calculator = SalaryCalculator(
            assignment
        )

        result = calculator.calculate()

        payroll = Payroll.objects.create(

            payroll_period=self.period,

            staff=staff,

            salary_assignment=assignment,

            deployment=deployment,

            gross_salary=result["gross_salary"],

            total_allowances=result["allowances"],

            total_deductions=result["deductions"],

            taxable_income=result["taxable_income"],

            tax_amount=result["tax"],

            pension_amount=result["pension"],

            nhf_amount=result["nhf"],

            loan_deduction=result["loan"],

            overtime_amount=result["overtime"],

            bonus_amount=result["bonus"],

            net_salary=result["net_salary"],

            processed_by=self.user,
        )

        for row in result["items"]:

            PayrollItem.objects.create(

                payroll=payroll,

                component=row["component"],

                description=row.get(
                    "description",
                    row["component"].name,
                ),

                quantity=row.get(
                    "quantity",
                    Decimal("1.00"),
                ),

                rate=row.get(
                    "rate",
                    Decimal("0.00"),
                ),
            )

        PayrollJournal.objects.create(

            payroll=payroll,

            narration=(
                f"{staff.full_name} "
                f"Salary - {self.period.period_name}"
            ),

            amount=payroll.net_salary,

            created_by=self.user,
        )

        PayrollPayment.objects.create(

            payroll=payroll,

            amount=payroll.net_salary,
        )

        Payslip.objects.create(

            payroll=payroll,

            generated_by=self.user,
        )

        return payroll