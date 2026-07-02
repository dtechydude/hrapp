import uuid
from decimal import Decimal

from django.db import models

from .payroll import Payroll


class PayrollJournal(models.Model):
    """
    Accounting journal generated from payroll.

    Every payroll creates one or more journal entries
    which can later be posted to the Accounting module.
    """

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )

    payroll = models.ForeignKey(
        Payroll,
        on_delete=models.CASCADE,
        related_name="journals",
    )

    account_name = models.CharField(
        max_length=150,
        help_text="Accounting account name.",
    )

    description = models.CharField(
        max_length=255,
        blank=True,
    )

    debit = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    credit = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:

        ordering = [
            "account_name",
        ]

        verbose_name = "Payroll Journal"

        verbose_name_plural = "Payroll Journals"

        indexes = [

            models.Index(fields=["payroll"]),

            models.Index(fields=["account_name"]),

        ]

    def __str__(self):
        return (
            f"{self.payroll.staff.full_name}"
            f" - "
            f"{self.account_name}"
        )

    @property
    def amount(self):
        """
        Returns the non-zero amount for display.
        """
        return self.debit if self.debit > 0 else self.credit

    @property
    def is_debit(self):
        return self.debit > 0

    @property
    def is_credit(self):
        return self.credit > 0