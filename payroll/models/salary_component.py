import uuid

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models

from .choices import (
    ComponentCalculation,
    ComponentType,
)

class ComponentCategory(models.TextChoices):

    BASIC = "BASIC", "Basic Salary"

    ALLOWANCE = "ALLOWANCE", "Allowance"

    DEDUCTION = "DEDUCTION", "Deduction"

    TAX = "TAX", "Tax"

    PENSION = "PENSION", "Pension"

    LOAN = "LOAN", "Loan"

    BONUS = "BONUS", "Bonus"

    OVERTIME = "OVERTIME", "Overtime"

    LEAVE = "LEAVE", "Leave"

    OTHER = "OTHER", "Other"



class SalaryComponent(models.Model):
    """
    Master list of all payroll components.

    Examples

    Basic Salary

    Housing

    PAYE

    Pension

    NHF

    Overtime

    Loan

    Bonus

    etc.
    """

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )

    code = models.CharField(
        max_length=20,
        unique=True,
        help_text="Unique component code e.g BASIC, HOUSING, PAYE",
    )

    name = models.CharField(
        max_length=150,
        unique=True,
    )

    category = models.CharField(
        max_length=20,
        choices=ComponentCategory.choices,
        default=ComponentCategory.OTHER,
    )

    component_type = models.CharField(
        max_length=20,
        choices=ComponentType.choices,
        default=ComponentType.OTHER,
    )

    calculation_method = models.CharField(
        max_length=20,
        choices=ComponentCalculation.choices,
        default=ComponentCalculation.FIXED,
    )

    default_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    percentage = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        help_text="Used when calculation method is Percentage.",
    )

    percentage_of = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="dependent_components",
        help_text="Component used as the base for percentage calculation."
    )

    apply_on_gross = models.BooleanField(
        default=False
    )

    allow_negative = models.BooleanField(
        default=False
    )

    is_taxable = models.BooleanField(
        default=False,
    )

    is_pensionable = models.BooleanField(
        default=False,
    )

    is_statutory = models.BooleanField(
        default=False,
        help_text="Government regulated deduction.",
    )

    affects_gross = models.BooleanField(
        default=True,
        help_text="Include in Gross Salary calculation.",
    )

    affects_net = models.BooleanField(
        default=True,
        help_text="Include in Net Salary calculation.",
    )

    is_active = models.BooleanField(
        default=True,
    )

    description = models.TextField(
        blank=True,
    )

    formula = models.CharField(
    max_length=255,
    blank=True,
    help_text=(
        "Optional calculation formula. "
        "Examples: BASIC * 0.08, "
        "GROSS * 0.025"
    ),
)

    display_order = models.PositiveSmallIntegerField(
        default=1,
    )

    is_editable = models.BooleanField(
        default=True,
        help_text="Can payroll officer edit amount during payroll?"
    )

    is_proratable = models.BooleanField(
        default=False,
        help_text="Should amount be prorated for incomplete month?"
    )

    show_on_payslip = models.BooleanField(
        default=True,
    )

    is_system = models.BooleanField(
        default=False,
        help_text="Protected system component."
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    created_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="salary_components_created",
    )

    updated_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="salary_components_updated",
    )

    class Meta:
        ordering = [
            "component_type",
            "name",
        ]

        verbose_name = "Salary Component"

        verbose_name_plural = "Salary Components"

        indexes = [           

            models.Index(fields=["code"]),

            models.Index(fields=["component_type"]),

            models.Index(fields=["display_order"]),

            models.Index(fields=["is_active"]),

        ]


        constraints = [

            models.UniqueConstraint(
                fields=["code"],
                name="unique_salary_component_code",
            ),

            models.UniqueConstraint(
                fields=["name"],
                name="unique_salary_component_name",
            ),

        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def clean(self):

        if (
            self.calculation_method == ComponentCalculation.PERCENTAGE
            and self.percentage <= 0
        ):
            raise ValidationError(
                "Percentage must be greater than zero."
            )

        if (
            self.calculation_method == ComponentCalculation.FIXED
            and self.default_amount < 0
        ):
            raise ValidationError(
                "Amount cannot be negative."
            )