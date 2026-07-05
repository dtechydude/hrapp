import uuid

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models

from employees.models import Staff

from .salary_structure import SalaryStructure


class SalaryChangeReason(models.TextChoices):
    APPOINTMENT = "Appointment", "Appointment"
    PROMOTION = "Promotion", "Promotion"
    ANNUAL_INCREMENT = "Annual Increment", "Annual Increment"
    SALARY_REVIEW = "Salary Review", "Salary Review"
    DEMOTION = "Demotion", "Demotion"
    TRANSFER = "Transfer", "Transfer"
    REINSTATEMENT = "Reinstatement", "Reinstatement"
    CONTRACT_RENEWAL = "Contract Renewal", "Contract Renewal"
    CORRECTION = "Correction", "Correction"
    OTHER = "Other", "Other"



class SalaryAssignment(models.Model):
    """
    Assigns a Salary Structure to an employee.

    Salary assignments are historical records and
    should never be edited after payroll has been run.
    """

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )

    staff = models.ForeignKey(
        Staff,
        on_delete=models.PROTECT,
        related_name="salary_assignments",
    )

    salary_structure = models.ForeignKey(
        SalaryStructure,
        on_delete=models.PROTECT,
        related_name="assigned_staff",
    )

    effective_from = models.DateField()

    effective_to = models.DateField(
        blank=True,
        null=True,
    )

    is_current = models.BooleanField(
        default=True,
        help_text="Current active salary assignment."
    )

    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="salary_assignments_approved",
    )

    # reason = models.CharField(
    #     max_length=200,
    #     blank=True,
    #     help_text="Promotion, Salary Review, Employment, etc."
    # )
    reason = models.CharField(
        max_length=30,
        choices=SalaryChangeReason.choices,
        default=SalaryChangeReason.APPOINTMENT,
    )

    remarks = models.TextField(
        blank=True,
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="salary_assignments_created",
    )

    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="salary_assignments_updated",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:

        ordering = (
            "-effective_from",
        )

        verbose_name = "Salary Assignment"

        verbose_name_plural = "Salary Assignments"

        indexes = [
            models.Index(fields=["staff"]),
            models.Index(fields=["salary_structure"]),
            models.Index(fields=["effective_from"]),
            models.Index(fields=["is_current"]),
        ]

        constraints = [

            models.UniqueConstraint(
                fields=[
                    "staff",
                    "effective_from",
                ],
                name="unique_salary_assignment_date",
            )

        ]

    def __str__(self):

        return (
            f"{self.staff} → "
            f"{self.salary_structure.name}"
        )

    def clean(self):

        if (
            self.effective_to
            and self.effective_to < self.effective_from
        ):
            raise ValidationError(
                "Effective To cannot be earlier than Effective From."
            )

    # def save(self, *args, **kwargs):

    #     """
    #     Only one active salary assignment
    #     per employee.
    #     """

    #     if self.is_current:

    #         SalaryAssignment.objects.filter(
    #             staff=self.staff,
    #             is_current=True,
    #         ).exclude(
    #             pk=self.pk
    #         ).update(
    #             is_current=False,
    #             effective_to=self.effective_from,
    #         )

    #     super().save(*args, **kwargs)

    def save(self, *args, **kwargs):
        """
        Snapshot Salary Component information.

        This ensures Payroll Items remain historically
        accurate even if the Salary Component changes
        after payroll has been processed.
        """

        self.full_clean()

        # Snapshot component details only when creating
        if self.component and not self.pk:
            self.component_name = self.component.name
            self.component_code = self.component.code
            self.component_type = self.component.component_type
            self.component_order = self.component.display_order

            self.is_taxable = self.component.is_taxable
            self.is_pensionable = self.component.is_pensionable
            self.is_statutory = self.component.is_statutory

        # Always calculate the amount from quantity × rate
        self.amount = self.quantity * self.rate

        super().save(*args, **kwargs)

    @property
    def gross_salary(self):
        return self.salary_structure.gross_salary

    @property
    def net_salary(self):
        return self.salary_structure.net_salary