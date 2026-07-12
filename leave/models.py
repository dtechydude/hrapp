"""
leave/models.py
───────────────────────────────────────────────────────────────────────────
Three models, deliberately normalized rather than hardcoding leave types
in code:

  LeaveType     — Annual, Sick, Maternity, etc. HR-configurable via admin,
                  not a Python enum, so new leave categories don't need a
                  code deploy.
  LeaveBalance  — per staff, per leave type, per year. Created lazily
                  (see services.py) the first time a staff member touches
                  a given leave type.
  LeaveRequest  — one row per application. Status transitions (Pending →
                  Approved/Declined/Cancelled) are the only mutation this
                  model allows after creation — the request itself is
                  never deleted, matching the project's "never overwrite
                  history" rule. days_requested is snapshotted at
                  submission time so a later change to how days are
                  calculated never rewrites past requests.
───────────────────────────────────────────────────────────────────────────
"""
import uuid as uuid_lib

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from employees.models import Staff


class LeaveType(models.Model):
    """HR-configurable leave category (Annual, Sick, Maternity, ...)."""

    name = models.CharField(max_length=60, unique=True)
    code = models.SlugField(max_length=20, unique=True, help_text="Short code, e.g. 'annual', 'sick'.")
    default_entitlement_days = models.PositiveSmallIntegerField(
        default=0,
        help_text="Days a staff member is entitled to per year for this leave type. "
                   "0 means untracked/unlimited (e.g. Compassionate Leave).",
    )
    requires_note = models.BooleanField(
        default=False,
        help_text="e.g. a medical note for Sick Leave — enforced at the UI level, not the DB level.",
    )
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Leave Type"

    def __str__(self) -> str:
        return self.name


class LeaveBalance(models.Model):
    """A staff member's entitlement/usage for one leave type in one year."""

    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="leave_balances")
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT, related_name="balances")
    year = models.PositiveSmallIntegerField(default=timezone.now().year)

    entitled_days = models.PositiveSmallIntegerField(default=0)
    used_days = models.PositiveSmallIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("staff", "leave_type", "year")
        ordering = ["leave_type__name"]
        verbose_name = "Leave Balance"
        verbose_name_plural = "Leave Balances"

    def __str__(self) -> str:
        return f"{self.staff.full_name} — {self.leave_type.name} ({self.year})"

    @property
    def remaining_days(self) -> int:
        return max(self.entitled_days - self.used_days, 0)


class LeaveRequestStatus(models.TextChoices):
    PENDING = "Pending", "Pending"
    APPROVED = "Approved", "Approved"
    DECLINED = "Declined", "Declined"
    CANCELLED = "Cancelled", "Cancelled"


class LeaveRequest(models.Model):
    """One leave application. Never deleted — only its status changes."""

    uuid = models.UUIDField(default=uuid_lib.uuid4, editable=False, unique=True, db_index=True)

    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="leave_requests")
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT, related_name="requests")

    start_date = models.DateField()
    end_date = models.DateField()
    days_requested = models.PositiveSmallIntegerField(
        editable=False,
        help_text="Snapshotted at submission time — never recalculated retroactively.",
    )
    reason = models.TextField()

    status = models.CharField(
        max_length=12, choices=LeaveRequestStatus.choices, default=LeaveRequestStatus.PENDING
    )

    applied_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_note = models.CharField(max_length=255, blank=True)

    # ── Standard audit columns (project-wide convention) ────────────
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        ordering = ["-applied_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["staff", "status"]),
        ]
        verbose_name = "Leave Request"

    def __str__(self) -> str:
        return f"{self.staff.full_name} — {self.leave_type.name} ({self.start_date} to {self.end_date})"

    def clean(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError("End date cannot be before the start date.")

    @property
    def is_pending(self) -> bool:
        return self.status == LeaveRequestStatus.PENDING

    @property
    def is_approved(self) -> bool:
        return self.status == LeaveRequestStatus.APPROVED
