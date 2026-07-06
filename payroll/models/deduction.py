from decimal import Decimal

from core.models import AuditableModel
from django.core.exceptions import ValidationError
from django.db import models

from employees.models import Staff

from .choices import ComponentNature, DeductionFrequency
from .payroll_period import PayrollPeriod
from .salary_component import SalaryComponent


class StaffDeduction(AuditableModel):
    """
    A standing instruction to deduct money from one staff member's
    pay — union dues, cooperative contribution, a court-ordered
    garnishment, etc.

    The payroll engine reads active, due StaffDeduction rows each run
    and creates a PayrollItem snapshot from each one; it never edits
    this row. Changing or deactivating a deduction here only affects
    FUTURE payroll runs — history already generated is untouched.
    """

    staff = models.ForeignKey(Staff, on_delete=models.PROTECT, related_name="deductions")
    component = models.ForeignKey(
        SalaryComponent, on_delete=models.PROTECT, related_name="staff_deductions"
    )

    frequency = models.CharField(
        max_length=20, choices=DeductionFrequency.choices, default=DeductionFrequency.RECURRING
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    start_date = models.DateField()
    end_date = models.DateField(
        null=True, blank=True, help_text="Leave blank for an open-ended recurring deduction."
    )

    reason = models.CharField(max_length=255, blank=True)
    is_suspended = models.BooleanField(
        default=False, help_text="Temporarily skip without deleting the instruction."
    )

    # Set by the payroll engine the moment a ONE-TIME deduction has
    # been applied, so it's never picked up again on a later run.
    applied_in_period = models.ForeignKey(
        PayrollPeriod,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="one_time_deductions_applied",
        editable=False,
    )

    class Meta:
        verbose_name = "Staff Deduction"
        verbose_name_plural = "Staff Deductions"
        ordering = ["-start_date"]
        indexes = [
            models.Index(fields=["staff", "is_active"]),
            models.Index(fields=["start_date"]),
        ]

    def __str__(self):
        return f"{self.staff.full_name} - {self.component.name} (₦{self.amount})"

    def clean(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError("End date cannot be before start date.")
        if self.component_id and self.component.nature != ComponentNature.DEDUCTION:
            raise ValidationError(
                {"component": "Only Deduction-nature components can be used here."}
            )

    def is_due_for(self, payroll_date) -> bool:
        """Whether this deduction should be applied for a given payroll date."""
        if self.is_suspended or not self.is_active:
            return False
        if payroll_date < self.start_date:
            return False
        if self.end_date and payroll_date > self.end_date:
            return False
        if self.frequency == DeductionFrequency.ONE_TIME and self.applied_in_period_id:
            return False
        return True

    def mark_applied(self, payroll_period):
        """Called by the payroll engine after a ONE-TIME deduction is applied."""
        if self.frequency == DeductionFrequency.ONE_TIME:
            self.applied_in_period = payroll_period
            self.save(update_fields=["applied_in_period", "updated_at"])
