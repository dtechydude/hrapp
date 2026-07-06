from decimal import Decimal

from core.models import AuditableModel
from django.core.exceptions import ValidationError
from django.db import models

from employees.models import Staff

from .choices import ComponentNature, DeductionFrequency
from .payroll_period import PayrollPeriod
from .salary_component import SalaryComponent


class StaffAllowance(AuditableModel):
    """
    A per-staff allowance layered on top of their salary structure —
    e.g. a one-off relocation allowance, or a recurring hazard
    allowance that only applies to specific individuals rather than
    an entire salary structure.

    Mirrors StaffDeduction's design deliberately: same
    recurring/one-time model, same "engine reads it, never edits it"
    contract, so both are handled identically inside the payroll
    engine's item-generation loop.
    """

    staff = models.ForeignKey(Staff, on_delete=models.PROTECT, related_name="allowances")
    component = models.ForeignKey(
        SalaryComponent, on_delete=models.PROTECT, related_name="staff_allowances"
    )

    frequency = models.CharField(
        max_length=20, choices=DeductionFrequency.choices, default=DeductionFrequency.RECURRING
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    reason = models.CharField(max_length=255, blank=True)
    is_suspended = models.BooleanField(default=False)

    applied_in_period = models.ForeignKey(
        PayrollPeriod,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="one_time_allowances_applied",
        editable=False,
    )

    class Meta:
        verbose_name = "Staff Allowance"
        verbose_name_plural = "Staff Allowances"
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
        if self.component_id and self.component.nature != ComponentNature.EARNING:
            raise ValidationError(
                {"component": "Only Earning-nature components can be used here."}
            )

    def is_due_for(self, payroll_date) -> bool:
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
        if self.frequency == DeductionFrequency.ONE_TIME:
            self.applied_in_period = payroll_period
            self.save(update_fields=["applied_in_period", "updated_at"])
