import uuid
from decimal import Decimal

from django.db import models
from django.contrib.auth.models import User

from .payroll_period import PayrollPeriod


class BankSchedule(models.Model):
    """
    Bank payment batch generated from a payroll period.

    One payroll period may produce one or more
    bank schedules if payments are split by bank.
    """

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )

    payroll_period = models.ForeignKey(
        PayrollPeriod,
        on_delete=models.PROTECT,
        related_name="bank_schedules",
    )

    schedule_number = models.CharField(
        max_length=30,
        unique=True,
        editable=False,
    )

    description = models.CharField(
        max_length=255,
        blank=True,
    )

    total_staff = models.PositiveIntegerField(
        default=0,
        editable=False,
    )

    total_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        editable=False,
    )

    exported = models.BooleanField(
        default=False,
    )

    exported_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    generated_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="generated_bank_schedules",
    )

    generated_at = models.DateTimeField(
        auto_now_add=True,
    )

    remarks = models.TextField(
        blank=True,
    )

    class Meta:

        ordering = [
            "-generated_at",
        ]

        verbose_name = "Bank Schedule"

        verbose_name_plural = "Bank Schedules"

        indexes = [

            models.Index(fields=["schedule_number"]),

            models.Index(fields=["generated_at"]),

        ]

    def __str__(self):
        return self.schedule_number

    def save(self, *args, **kwargs):

        if not self.schedule_number:

            period = self.payroll_period

            last = BankSchedule.objects.order_by("-id").first()

            number = 1 if not last else last.id + 1

            self.schedule_number = (
                f"BS-"
                f"{period.year}-"
                f"{period.month:02d}-"
                f"{number:05d}"
            )

        super().save(*args, **kwargs)

    def update_totals(self):

        totals = self.items.aggregate(

            total=models.Sum("amount"),

            count=models.Count("id"),

        )

        self.total_staff = totals["count"] or 0

        self.total_amount = totals["total"] or Decimal("0.00")

        self.save(
            update_fields=[
                "total_staff",
                "total_amount",
            ]
        )