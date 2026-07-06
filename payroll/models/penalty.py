from decimal import Decimal

from core.models import AuditableModel
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from employees.models import Staff

from .choices import ComponentNature, RequestStatus
from .payroll_period import PayrollPeriod
from .salary_component import SalaryComponent


class Penalty(AuditableModel):
    """
    A disciplinary or attendance-driven deduction (late arrival,
    policy breach, damage recovery, etc.). Mirrors Bonus's
    approve/reject/apply-once lifecycle so both flow through the
    payroll engine the same way.
    """

    staff = models.ForeignKey(Staff, on_delete=models.PROTECT, related_name="penalties")
    component = models.ForeignKey(
        SalaryComponent, on_delete=models.PROTECT, related_name="staff_penalties"
    )

    amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    reason = models.CharField(max_length=255)

    target_period = models.ForeignKey(
        PayrollPeriod,
        on_delete=models.PROTECT,
        related_name="penalties",
        help_text="The payroll period this penalty should be deducted in.",
    )

    status = models.CharField(max_length=20, choices=RequestStatus.choices, default=RequestStatus.PENDING)
    imposed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="penalties_imposed",
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="penalties_approved",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    comments = models.TextField(blank=True)

    applied_in_period = models.ForeignKey(
        PayrollPeriod,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="penalties_applied",
        editable=False,
    )

    class Meta:
        verbose_name = "Penalty"
        verbose_name_plural = "Penalties"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["staff", "status"]),
            models.Index(fields=["target_period"]),
        ]

    def __str__(self):
        return f"{self.staff.full_name} - Penalty ₦{self.amount} ({self.target_period})"

    def clean(self):
        if self.component_id and self.component.nature != ComponentNature.DEDUCTION:
            raise ValidationError({"component": "Penalty component must be Deduction-nature."})
        if self.amount <= 0:
            raise ValidationError({"amount": "Penalty amount must be greater than zero."})

    @property
    def is_approved(self) -> bool:
        return self.status == RequestStatus.APPROVED

    @property
    def is_due(self) -> bool:
        return self.is_approved and self.applied_in_period_id is None

    def approve(self, user, comments: str = ""):
        self.status = RequestStatus.APPROVED
        self.approved_by = user
        self.approved_at = timezone.now()
        self.comments = comments
        self.save(update_fields=["status", "approved_by", "approved_at", "comments", "updated_at"])

    def reject(self, user, comments: str = ""):
        self.status = RequestStatus.REJECTED
        self.approved_by = user
        self.approved_at = timezone.now()
        self.comments = comments
        self.save(update_fields=["status", "approved_by", "approved_at", "comments", "updated_at"])

    def mark_applied(self, payroll_period):
        self.applied_in_period = payroll_period
        self.save(update_fields=["applied_in_period", "updated_at"])
