from decimal import Decimal

from core.models import AuditableModel
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from employees.models import Staff

from .choices import AdvanceStatus, ComponentNature
from .salary_component import SalaryComponent


class SalaryAdvance(AuditableModel):
    """
    A short-term advance against future salary, repaid over one or
    more payroll periods via automatic deductions — distinct from the
    formal Staff Loans handled by the separate `loan` app, which
    covers larger, interest-bearing facilities.
    """

    staff = models.ForeignKey(Staff, on_delete=models.PROTECT, related_name="salary_advances")
    component = models.ForeignKey(
        SalaryComponent, on_delete=models.PROTECT, related_name="staff_advances"
    )

    amount_requested = models.DecimalField(max_digits=12, decimal_places=2)
    amount_approved = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    monthly_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), editable=False)

    reason = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=AdvanceStatus.choices, default=AdvanceStatus.PENDING)

    requested_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="salary_advances_approved",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    comments = models.TextField(blank=True)

    class Meta:
        verbose_name = "Salary Advance"
        verbose_name_plural = "Salary Advances"
        ordering = ["-requested_at"]
        indexes = [
            models.Index(fields=["staff", "status"]),
        ]

    def __str__(self):
        return f"{self.staff.full_name} - Advance ₦{self.amount_requested} ({self.status})"

    def clean(self):
        if self.component_id and self.component.nature != ComponentNature.DEDUCTION:
            raise ValidationError({"component": "Advance repayment component must be Deduction-nature."})
        if self.amount_requested <= 0:
            raise ValidationError({"amount_requested": "Amount must be greater than zero."})

    @property
    def is_active_advance(self) -> bool:
        return self.status == AdvanceStatus.ACTIVE and self.balance > 0

    def approve(self, user, amount_approved, monthly_deduction, comments: str = ""):
        """
        Approves the advance and opens the repayment balance. Doesn't
        touch payroll — the engine picks this up as ACTIVE with a
        remaining balance on the next run it's due.
        """
        self.status = AdvanceStatus.ACTIVE
        self.amount_approved = amount_approved
        self.monthly_deduction = monthly_deduction
        self.balance = amount_approved
        self.approved_by = user
        self.approved_at = timezone.now()
        self.comments = comments
        self.save(
            update_fields=[
                "status", "amount_approved", "monthly_deduction", "balance",
                "approved_by", "approved_at", "comments", "updated_at",
            ]
        )

    def reject(self, user, comments: str = ""):
        self.status = AdvanceStatus.REJECTED
        self.approved_by = user
        self.approved_at = timezone.now()
        self.comments = comments
        self.save(update_fields=["status", "approved_by", "approved_at", "comments", "updated_at"])

    def next_deduction_amount(self) -> Decimal:
        """The amount to deduct this run — the standard installment,
        capped at whatever balance remains (final installment)."""
        return min(self.monthly_deduction, self.balance)

    def record_repayment(self, amount: Decimal, payroll):
        """
        Records one payroll deduction against this advance. Creates a
        permanent AdvanceRepayment row (financial history is never
        overwritten) and decrements the live balance. Settles the
        advance automatically once the balance reaches zero.
        """
        if amount <= 0 or amount > self.balance:
            raise ValidationError("Invalid repayment amount for this advance.")

        AdvanceRepayment.objects.create(advance=self, payroll=payroll, amount=amount)

        self.balance -= amount
        if self.balance <= 0:
            self.balance = Decimal("0.00")
            self.status = AdvanceStatus.SETTLED
        self.save(update_fields=["balance", "status", "updated_at"])


class AdvanceRepayment(models.Model):
    """
    One payroll-deduction installment against a SalaryAdvance.
    Permanent, immutable financial record — never edited or deleted,
    even if the parent advance is later settled or written off.
    """

    advance = models.ForeignKey(SalaryAdvance, on_delete=models.PROTECT, related_name="repayments")
    payroll = models.ForeignKey(
        "payroll.Payroll", on_delete=models.PROTECT, related_name="advance_repayments"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Advance Repayment"
        verbose_name_plural = "Advance Repayments"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["advance", "payroll"], name="unique_advance_repayment_per_payroll")
        ]

    def __str__(self):
        return f"{self.advance.staff.full_name} - ₦{self.amount} repayment"
