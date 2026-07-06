import uuid

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models

from .choices import ComponentCalculation, ComponentCategory, ComponentNature


class SalaryComponent(models.Model):
    """
    Master list of all payroll components — Basic Salary, Housing,
    PAYE, Pension, NHF, Overtime, Loan, Bonus, etc.

    `category` answers "what kind of thing is this" (for grouping on
    payslips/reports). `nature` answers "does it add or subtract from
    pay" (for gross/net arithmetic). Keeping these separate avoids the
    duplicated-taxonomy problem in the original draft.
    """

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    code = models.CharField(
        max_length=20,
        unique=True,
        help_text="Unique component code e.g BASIC, HOUSING, PAYE",
    )

    name = models.CharField(max_length=150, unique=True)

    category = models.CharField(
        max_length=20,
        choices=ComponentCategory.choices,
        default=ComponentCategory.OTHER,
    )

    nature = models.CharField(
        max_length=20,
        choices=ComponentNature.choices,
        default=ComponentNature.EARNING,
        help_text="Whether this component adds to or subtracts from pay.",
    )

    calculation_method = models.CharField(
        max_length=20,
        choices=ComponentCalculation.choices,
        default=ComponentCalculation.FIXED,
    )

    default_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

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
        help_text=(
            "Component used as the base for percentage calculation. "
            "Leave blank to calculate as a percentage of Gross Salary "
            "so far (see apply_on_gross)."
        ),
    )

    apply_on_gross = models.BooleanField(
        default=False,
        help_text="If Percentage and no percentage_of is set, base the percentage on gross salary.",
    )

    allow_negative = models.BooleanField(default=False)
    is_taxable = models.BooleanField(default=False)
    is_pensionable = models.BooleanField(default=False)
    is_statutory = models.BooleanField(
        default=False, help_text="Government regulated deduction."
    )
    affects_gross = models.BooleanField(
        default=True, help_text="Include in Gross Salary calculation."
    )
    affects_net = models.BooleanField(
        default=True, help_text="Include in Net Salary calculation."
    )
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)

    formula = models.CharField(
        max_length=255,
        blank=True,
        help_text=(
            "Only used when calculation method is Formula. Supports "
            "+ - * / and parentheses, referencing other component "
            "codes already calculated for this staff member this "
            "payroll, e.g. 'BASIC * 0.08' or 'BASIC + HOUSING'. "
            "Evaluated by a restricted parser — never Python eval()."
        ),
    )

    display_order = models.PositiveSmallIntegerField(default=1)
    is_editable = models.BooleanField(
        default=True, help_text="Can payroll officer edit amount during payroll?"
    )
    is_proratable = models.BooleanField(
        default=False, help_text="Should amount be prorated for incomplete month?"
    )
    show_on_payslip = models.BooleanField(default=True)
    is_system = models.BooleanField(default=False, help_text="Protected system component.")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="salary_components_created",
    )
    updated_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="salary_components_updated",
    )

    class Meta:
        ordering = ["category", "display_order", "name"]
        verbose_name = "Salary Component"
        verbose_name_plural = "Salary Components"
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["category"]),
            models.Index(fields=["nature"]),
            models.Index(fields=["display_order"]),
            models.Index(fields=["is_active"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["code"], name="unique_salary_component_code"),
            models.UniqueConstraint(fields=["name"], name="unique_salary_component_name"),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def clean(self):
        if self.calculation_method == ComponentCalculation.PERCENTAGE and self.percentage <= 0:
            raise ValidationError("Percentage must be greater than zero.")

        if self.calculation_method == ComponentCalculation.FIXED and self.default_amount < 0:
            raise ValidationError("Amount cannot be negative.")

        if self.calculation_method == ComponentCalculation.FORMULA and not self.formula:
            raise ValidationError("Formula is required when calculation method is Formula.")

        if self.percentage_of_id and self.percentage_of_id == self.id:
            raise ValidationError("A component cannot be a percentage of itself.")

    @property
    def is_earning(self) -> bool:
        return self.nature == ComponentNature.EARNING

    @property
    def is_deduction(self) -> bool:
        return self.nature == ComponentNature.DEDUCTION
