import uuid
from decimal import Decimal

from django.db import models

from employees.models import Staff

from .bank_schedule import BankSchedule


class BankScheduleItem(models.Model):
    """
    Individual employee payment line
    in a bank schedule.
    """

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )

    schedule = models.ForeignKey(
        BankSchedule,
        on_delete=models.CASCADE,
        related_name="items",
    )

    staff = models.ForeignKey(
        Staff,
        on_delete=models.PROTECT,
        related_name="bank_schedule_items",
    )

    account_name = models.CharField(
        max_length=150,
    )

    account_number = models.CharField(
        max_length=20,
    )

    bank_name = models.CharField(
        max_length=100,
    )

    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    narration = models.CharField(
        max_length=255,
        blank=True,
    )

    class Meta:

        ordering = [
            "staff__user__last_name",
        ]

        verbose_name = "Bank Schedule Item"

        verbose_name_plural = "Bank Schedule Items"

        constraints = [

            models.UniqueConstraint(
                fields=[
                    "schedule",
                    "staff",
                ],
                name="unique_staff_bank_schedule",
            )

        ]

    def __str__(self):

        return (
            f"{self.staff.full_name} "
            f"- ₦{self.amount}"
        )

    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)

        self.schedule.update_totals()

    def delete(self, *args, **kwargs):

        schedule = self.schedule

        super().delete(*args, **kwargs)

        schedule.update_totals()