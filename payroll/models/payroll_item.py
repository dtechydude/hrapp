import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models

from .payroll import Payroll
from .salary_component import SalaryComponent


class PayrollItem(models.Model):
    """
    Individual Payroll Line Item.

    Stores every earning and deduction generated during payroll
    processing. This model acts as the permanent historical
    breakdown used for Payslips, Payroll Reports and Accounting.

    IMPORTANT:
    The component information is snapshotted when the PayrollItem
    is first created. This ensures historical payroll records
    remain unchanged even if Salary Components are edited later.
    """

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )

    payroll = models.ForeignKey(
        Payroll,
        on_delete=models.CASCADE,
        related_name="items",
    )

    component = models.ForeignKey(
        SalaryComponent,
        on_delete=models.PROTECT,
        related_name="payroll_items",
    )

    description = models.CharField(
        max_length=255,
        blank=True,
    )

    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("1.00"),
        help_text="Useful for overtime, days worked, hours worked etc.",
    )

    rate = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Rate per unit.",
    )

    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        editable=False,
    )

    # -------------------------------------------------
    # Snapshot fields
    # These preserve historical payroll integrity.
    # -------------------------------------------------

    component_name = models.CharField(
        max_length=100,
        editable=False,
    )

    component_code = models.CharField(
        max_length=30,
        editable=False,
    )

    component_order = models.PositiveSmallIntegerField(
        default=0,
        editable=False,
    )

    is_taxable = models.BooleanField(
        default=False,
    )

    is_pensionable = models.BooleanField(
        default=False,
    )

    is_statutory = models.BooleanField(
        default=False,
        help_text="Government statutory deduction.",
    )

    remarks = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:

        verbose_name = "Payroll Item"
        verbose_name_plural = "Payroll Items"

        ordering = (
            "component_order",
            "component_name",
        )

        constraints = [

            models.UniqueConstraint(
                fields=[
                    "payroll",
                    "component",
                ],
                name="unique_payroll_component",
            ),

        ]

        indexes = [

            models.Index(fields=["payroll"]),
            models.Index(fields=["component"]),
            models.Index(fields=["component_code"]),

        ]

    # -------------------------------------------------
    # Object Representation
    # -------------------------------------------------

    def __str__(self):
        return (
            f"{self.payroll.staff.full_name} - "
            f"{self.component_name}"
        )

    # -------------------------------------------------
    # Validation
    # -------------------------------------------------

    def clean(self):
        """
        Business validation.
        """

        if self.quantity < 0:
            raise ValidationError(
                {"quantity": "Quantity cannot be negative."}
            )

        if self.rate < 0:
            raise ValidationError(
                {"rate": "Rate cannot be negative."}
            )

    # -------------------------------------------------
    # Save Logic
    # -------------------------------------------------

    def save(self, *args, **kwargs):
        """
        Snapshot Salary Component information.

        This ensures Payroll Items remain historically
        accurate even if the Salary Component changes
        in future.
        """

        self.full_clean()

        if self.component and not self.pk:

            self.component_name = self.component.name
            self.component_code = self.component.code
            self.component_order = self.component.display_order

            self.is_taxable = self.component.is_taxable
            self.is_pensionable = self.component.is_pensionable
            self.is_statutory = self.component.is_statutory

        self.amount = self.quantity * self.rate

        super().save(*args, **kwargs)

    # -------------------------------------------------
    # Helper Properties
    # -------------------------------------------------

    @property
    def total(self):
        """
        Returns the calculated amount.
        """
        return self.quantity * self.rate

    @property
    def is_earning(self):
        """
        Returns True if this item is an earning.
        """
        return (
            self.component.component_type
            == SalaryComponent.ComponentType.EARNING
        )

    @property
    def is_deduction(self):
        """
        Returns True if this item is a deduction.
        """
        return (
            self.component.component_type
            == SalaryComponent.ComponentType.DEDUCTION
        )