import uuid
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum

from organization.models import Company

from .choices import ComponentNature
from .salary_component import SalaryComponent


class SalaryStructure(models.Model):
    """
    Salary template assigned to one or more employees.

    Example: Graduate Trainee, Senior Accountant, Security Officer
    Grade II, Driver Level 4.
    """

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="salary_structures")

    name = models.CharField(max_length=150)
    code = models.CharField(max_length=30, unique=True, help_text="Example: SS001")
    description = models.TextField(blank=True)

    effective_from = models.DateField()
    effective_to = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    created_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="salary_structures_created",
    )
    updated_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="salary_structures_updated",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Salary Structure"
        verbose_name_plural = "Salary Structures"
        constraints = [
            models.UniqueConstraint(fields=["company", "name"], name="unique_company_salary_structure")
        ]
        indexes = [
            models.Index(fields=["company"]),
            models.Index(fields=["name"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.company} - {self.name}"

    @property
    def gross_salary(self) -> Decimal:
        total = self.items.filter(
            component__affects_gross=True
        ).aggregate(total=Sum("amount"))["total"]
        return total or Decimal("0.00")

    @property
    def total_deduction(self) -> Decimal:
        total = self.items.filter(
            component__nature=ComponentNature.DEDUCTION
        ).aggregate(total=Sum("amount"))["total"]
        return total or Decimal("0.00")

    @property
    def net_salary(self) -> Decimal:
        return self.gross_salary - self.total_deduction

    def clean(self):
        if self.effective_to and self.effective_to < self.effective_from:
            raise ValidationError("Effective To cannot be earlier than Effective From.")


class SalaryStructureItem(models.Model):
    """
    One line in a salary structure template — e.g. Basic Salary,
    Housing, Transport, PAYE, Pension, NHF.
    """

    salary_structure = models.ForeignKey(SalaryStructure, on_delete=models.CASCADE, related_name="items")
    component = models.ForeignKey(SalaryComponent, on_delete=models.PROTECT, related_name="salary_items")

    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    percentage = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    formula_override = models.CharField(
        max_length=255, blank=True, help_text="Optional custom formula for this structure."
    )
    display_order = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ["display_order", "component__name"]
        verbose_name = "Salary Structure Item"
        verbose_name_plural = "Salary Structure Items"
        constraints = [
            models.UniqueConstraint(
                fields=["salary_structure", "component"], name="unique_salary_component"
            )
        ]

    def __str__(self):
        return f"{self.salary_structure.name} - {self.component.name}"
