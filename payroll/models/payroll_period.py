import uuid

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from organization.models import Company

from .choices import PayrollMonth, PayrollStatus


class PayrollPeriod(models.Model):
    """
    Represents a monthly payroll processing period.

    Every payroll record, payslip, deduction and payment
    belongs to one payroll period.
    """

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )

    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        related_name="payroll_periods",
        help_text="Payroll batch for this company.",
    )

    month = models.PositiveSmallIntegerField(
        choices=PayrollMonth.choices,
    )

    year = models.PositiveIntegerField()

    status = models.CharField(
        max_length=20,
        choices=PayrollStatus.choices,
        default=PayrollStatus.DRAFT,
    )

    payroll_date = models.DateField(
        help_text="Official payroll date."
    )

    opened_at = models.DateTimeField(
        auto_now_add=True,
    )

    approved_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    paid_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    locked_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    generated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="generated_payroll_periods",
    )

    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_payroll_periods",
    )

    locked_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="locked_payroll_periods",
    )

    remarks = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        ordering = (
            "-year",
            "-month",
        )

        verbose_name = "Payroll Period"
        verbose_name_plural = "Payroll Periods"

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "company",
                    "month",
                    "year",
                ],
                name="unique_company_payroll_period",
            )
        ]

        indexes = [
            models.Index(fields=["company"]),
            models.Index(fields=["month"]),
            models.Index(fields=["year"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.company} - {self.get_month_display()} {self.year}"

    def clean(self):
        """
        Prevent creation of payroll for future years.
        """

        current_year = timezone.now().year

        if self.year < 2020:
            raise ValidationError(
                "Payroll year is invalid."
            )

        if self.year > current_year + 1:
            raise ValidationError(
                "Payroll year cannot be far into the future."
            )

    @property
    def period_name(self):
        return f"{self.get_month_display()} {self.year}"

    @property
    def is_locked(self):
        return self.status == PayrollStatus.LOCKED

    @property
    def is_paid(self):
        return self.status == PayrollStatus.PAID

    @property
    def is_approved(self):
        return self.status == PayrollStatus.APPROVED

    def approve(self, user):
        """
        Approve payroll.
        """

        self.status = PayrollStatus.APPROVED
        self.approved_by = user
        self.approved_at = timezone.now()

        self.save(
            update_fields=[
                "status",
                "approved_by",
                "approved_at",
            ]
        )

    def mark_as_paid(self):
        """
        Payroll successfully paid.
        """

        self.status = PayrollStatus.PAID
        self.paid_at = timezone.now()

        self.save(
            update_fields=[
                "status",
                "paid_at",
            ]
        )

    def lock(self, user):
        """
        Lock payroll forever.

        Locked payroll cannot be modified.
        """

        self.status = PayrollStatus.LOCKED
        self.locked_by = user
        self.locked_at = timezone.now()

        self.save(
            update_fields=[
                "status",
                "locked_by",
                "locked_at",
            ]
        )

    # def lock(self):
    #     self.locked = True
    #     self.save(update_fields=["locked"])

    def unlock(self):
        self.locked = False
        self.save(update_fields=["locked"])