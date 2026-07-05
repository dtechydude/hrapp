import uuid
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from employees.models import Staff
from organization.models import StaffDeployment

from .choices import PaymentMethod, PaymentStatus
from .payroll_period import PayrollPeriod
from .salary_assignment import SalaryAssignment


class Payroll(models.Model):
    """
    Payroll Header.

    Represents one employee's payroll for a payroll period.

    The detailed earnings and deductions are stored
    in PayrollItem.
    """

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )

    payroll_period = models.ForeignKey(
        PayrollPeriod,
        on_delete=models.PROTECT,
        related_name="payrolls",
    )

    staff = models.ForeignKey(
        Staff,
        on_delete=models.PROTECT,
        related_name="payrolls",
    )

    salary_assignment = models.ForeignKey(
        SalaryAssignment,
        on_delete=models.PROTECT,
        related_name="payrolls",
    )

    deployment = models.ForeignKey(
        StaffDeployment,
        on_delete=models.PROTECT,
        related_name="payrolls",
        help_text="Deployment used when payroll was generated."
    )

    # =============================
    # Payroll Summary
    # =============================

    gross_salary = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    total_earnings = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    total_deductions = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    taxable_income = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    net_salary = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    # =============================
    # Payment
    # =============================

    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        blank=True,
    )

    payment_reference = models.CharField(
        max_length=150,
        blank=True,
    )

    payment_date = models.DateTimeField(
        null=True,
        blank=True,
    )

    # =============================
    # Approval Workflow
    # =============================

    processed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="processed_payrolls",
    )

    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_payrolls",
    )

    approved_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    remarks = models.TextField(
        blank=True,
    )

    calculated_at = models.DateTimeField(
    auto_now_add=True,
    )

    locked = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:

        ordering = (
            "-payroll_period__year",
            "-payroll_period__month",
            "staff__user__last_name",
        )

        verbose_name = "Payroll"

        verbose_name_plural = "Payroll"

        constraints = [

            models.UniqueConstraint(
                fields=[
                    "payroll_period",
                    "staff",
                ],
                name="unique_staff_payroll",
            )

        ]

        indexes = [

            models.Index(fields=["staff"]),
            models.Index(fields=["payroll_period"]),
            models.Index(fields=["payment_status"]),

        ]

    def __str__(self):

        return (
            f"{self.staff.full_name}"
            f" - "
            f"{self.payroll_period.period_name}"
        )

    def clean(self):

        if self.salary_assignment.staff != self.staff:
            raise ValidationError(
                "Selected Salary Assignment does not belong to the selected employee."
            )

    @property
    def is_paid(self):
        return self.payment_status == PaymentStatus.PAID

    @property
    def outstanding_amount(self):

        if self.is_paid:
            return Decimal("0.00")

        return self.net_salary

    def mark_as_paid(
        self,
        payment_method,
        reference,
        user,
    ):

        self.payment_status = PaymentStatus.PAID
        self.payment_method = payment_method
        self.payment_reference = reference
        self.payment_date = timezone.now()

        self.approved_by = user
        self.approved_at = timezone.now()

        self.save(
            update_fields=[
                "payment_status",
                "payment_method",
                "payment_reference",
                "payment_date",
                "approved_by",
                "approved_at",
            ]
        )