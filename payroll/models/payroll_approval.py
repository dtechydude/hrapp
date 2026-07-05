import uuid

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone

from .payroll import Payroll
from .choices import  ApprovalLevel, ApprovalStatus


class PayrollApproval(models.Model):
    """
    Payroll approval workflow.

    Every payroll record can pass through
    multiple approval stages.

    The history is never deleted.

    One Payroll
            ↓
    Payroll Officer
            ↓
    HR Manager
            ↓
    Finance Manager
            ↓
    Managing Director
    """

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )


    payroll = models.ForeignKey(
        Payroll,
        on_delete=models.CASCADE,
        related_name="approvals",
    )

    level = models.CharField(
        max_length=30,
        choices=ApprovalLevel.choices,
    )

    status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING,
    )

    assigned_to = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_payroll_approvals",
    )

    approved_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="approved_payroll_steps",
    )

    rejected_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="rejected_payroll_steps",
    )

    assigned_at = models.DateTimeField(
        auto_now_add=True,
    )

    action_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    comments = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:

        ordering = [
            "created_at",
        ]

        verbose_name = "Payroll Approval"

        verbose_name_plural = "Payroll Approvals"

        constraints = [

            models.UniqueConstraint(
                fields=[
                    "payroll",
                    "level",
                ],
                name="unique_payroll_approval_level",
            )

        ]

        indexes = [

            models.Index(fields=["status"]),

            models.Index(fields=["level"]),

            models.Index(fields=["payroll"]),

        ]

    def __str__(self):

        return (
            f"{self.payroll.staff.full_name}"
            f" - "
            f"{self.get_level_display()}"
        )

    def clean(self):

        super().clean()

        if (
            self.status == ApprovalStatus.APPROVED
            and not self.approved_by
        ):
            raise ValidationError(
                {
                    "approved_by":
                    "Approver is required."
                }
            )

        if (
            self.status == ApprovalStatus.REJECTED
            and not self.rejected_by
        ):
            raise ValidationError(
                {
                    "rejected_by":
                    "Rejecting user is required."
                }
            )

    def save(self, *args, **kwargs):

        self.full_clean()

        super().save(*args, **kwargs)


    def approve(self, user, comments=""):

        self.status = ApprovalStatus.APPROVED

        self.approved_by = user

        self.action_at = timezone.now()

        self.comments = comments

        self.save()

    def reject(self, user, comments=""):

        self.status = ApprovalStatus.REJECTED

        self.rejected_by = user

        self.action_at = timezone.now()

        self.comments = comments

        self.save()

    @property
    def is_pending(self):
        return self.status == ApprovalStatus.PENDING


    @property
    def is_approved(self):
        return self.status == ApprovalStatus.APPROVED


    @property
    def is_rejected(self):
        return self.status == ApprovalStatus.REJECTED