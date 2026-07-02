import uuid

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

from .payroll_period import PayrollPeriod


class PayrollRun(models.Model):
    """
    Records every payroll processing event.

    A Payroll Period may be processed
    multiple times before final approval.

    Once approved,
    the last successful run becomes official.
    """

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )

    payroll_period = models.ForeignKey(
        PayrollPeriod,
        on_delete=models.CASCADE,
        related_name="runs",
    )

    run_number = models.PositiveIntegerField()

    started_at = models.DateTimeField(
        auto_now_add=True,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    started_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="started_payroll_runs",
    )

    total_staff = models.PositiveIntegerField(
        default=0,
    )

    successful = models.PositiveIntegerField(
        default=0,
    )

    failed = models.PositiveIntegerField(
        default=0,
    )

    remarks = models.TextField(
        blank=True,
    )

    is_completed = models.BooleanField(
        default=False,
    )

    class Meta:

        ordering = [
            "-started_at",
        ]

        constraints = [

            models.UniqueConstraint(
                fields=[
                    "payroll_period",
                    "run_number",
                ],
                name="unique_payroll_run",
            )

        ]

    def __str__(self):

        return (
            f"{self.payroll_period.period_name}"
            f" Run {self.run_number}"
        )

    def complete(self):

        self.is_completed = True

        self.completed_at = timezone.now()

        self.save(
            update_fields=[
                "is_completed",
                "completed_at",
            ]
        )