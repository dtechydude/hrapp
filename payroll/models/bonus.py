from decimal import Decimal

from core.models import AuditableModel
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from django.conf import settings
from employees.models import Staff

from .choices import ComponentNature, RequestStatus
from .payroll_period import PayrollPeriod
from .salary_component import SalaryComponent


class Bonus(AuditableModel):
    """
    A one-time bonus award for a staff member. Requires approval
    before the payroll engine will roll it into a payroll run —
    unapproved bonuses are simply invisible to payroll generation.
    """

    staff = models.ForeignKey(Staff, on_delete=models.PROTECT, related_name="bonuses")
    component = models.ForeignKey(
        SalaryComponent, on_delete=models.PROTECT, related_name="staff_bonuses"
    )

    amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    reason = models.CharField(max_length=255)

    target_period = models.ForeignKey(
        PayrollPeriod,
        on_delete=models.PROTECT,
        related_name="bonuses",
        help_text="The payroll period this bonus should be paid in.",
    )

    status = models.CharField(max_length=20, choices=RequestStatus.choices, default=RequestStatus.PENDING)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="bonuses_requested",
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="bonuses_approved",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    comments = models.TextField(blank=True)

    # Set once the payroll engine has actually included this bonus in
    # a run, so it's never applied twice even if the run is re-triggered.
    applied_in_period = models.ForeignKey(
        PayrollPeriod,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="bonuses_applied",
        editable=False,
    )

    class Meta:
        verbose_name = "Bonus"
        verbose_name_plural = "Bonuses"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["staff", "status"]),
            models.Index(fields=["target_period"]),
        ]

    def __str__(self):
        return f"{self.staff.full_name} - Bonus ₦{self.amount} ({self.target_period})"

    def clean(self):
        if self.component_id and self.component.nature != ComponentNature.EARNING:
            raise ValidationError({"component": "Bonus component must be Earning-nature."})
        if self.amount <= 0:
            raise ValidationError({"amount": "Bonus amount must be greater than zero."})

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
