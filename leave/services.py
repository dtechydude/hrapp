"""
leave/services.py
───────────────────────────────────────────────────────────────────────────
All leave business rules live here. Views only orchestrate; they never
touch balance math or status transitions directly.
───────────────────────────────────────────────────────────────────────────
"""
from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import LeaveBalance, LeaveRequest, LeaveRequestStatus, LeaveType


def calculate_days(start_date, end_date) -> int:
    """
    Inclusive calendar-day count between two dates.

    Deliberately simple (counts weekends) so behavior is predictable and
    transparent to staff applying for leave. If your policy needs
    working-day-only counting (skip Sat/Sun, public holidays), swap the
    body of this function — every caller goes through it, so the change
    is one-line to make project-wide.
    """
    if not start_date or not end_date or end_date < start_date:
        raise ValidationError("End date cannot be before the start date.")
    return (end_date - start_date).days + 1


def get_or_create_balance(staff, leave_type: LeaveType, year: int | None = None) -> LeaveBalance:
    """
    Lazily creates a LeaveBalance the first time a staff member touches a
    given leave type/year, seeded from LeaveType.default_entitlement_days.
    """
    year = year or timezone.localdate().year
    balance, _ = LeaveBalance.objects.get_or_create(
        staff=staff,
        leave_type=leave_type,
        year=year,
        defaults={"entitled_days": leave_type.default_entitlement_days},
    )
    return balance


@transaction.atomic
def submit_request(staff, leave_type: LeaveType, start_date, end_date, reason: str) -> LeaveRequest:
    """
    Creates a Pending LeaveRequest for `staff`. Raises ValidationError if
    the request would exceed the staff member's remaining balance for a
    *tracked* leave type (default_entitlement_days > 0). Untracked types
    (default_entitlement_days == 0, e.g. Compassionate Leave) skip the
    balance check entirely.
    """
    days = calculate_days(start_date, end_date)

    if leave_type.default_entitlement_days > 0:
        balance = get_or_create_balance(staff, leave_type, start_date.year)
        if days > balance.remaining_days:
            raise ValidationError(
                f"You only have {balance.remaining_days} day(s) of {leave_type.name} remaining "
                f"this year, but requested {days}."
            )

    leave_request = LeaveRequest.objects.create(
        staff=staff,
        leave_type=leave_type,
        start_date=start_date,
        end_date=end_date,
        days_requested=days,
        reason=reason,
        status=LeaveRequestStatus.PENDING,
        created_by=getattr(staff, "user", None),
        updated_by=getattr(staff, "user", None),
    )
    return leave_request


@transaction.atomic
def approve_request(leave_request: LeaveRequest, approved_by, note: str = "") -> LeaveRequest:
    if not leave_request.is_pending:
        raise ValidationError("Only pending requests can be approved.")

    if leave_request.leave_type.default_entitlement_days > 0:
        balance = get_or_create_balance(leave_request.staff, leave_request.leave_type, leave_request.start_date.year)
        balance.used_days += leave_request.days_requested
        balance.save(update_fields=["used_days", "updated_at"])

    leave_request.status = LeaveRequestStatus.APPROVED
    leave_request.reviewed_by = approved_by
    leave_request.reviewed_at = timezone.now()
    leave_request.review_note = note
    leave_request.updated_by = approved_by
    leave_request.save()
    return leave_request


@transaction.atomic
def decline_request(leave_request: LeaveRequest, declined_by, note: str = "") -> LeaveRequest:
    if not leave_request.is_pending:
        raise ValidationError("Only pending requests can be declined.")

    leave_request.status = LeaveRequestStatus.DECLINED
    leave_request.reviewed_by = declined_by
    leave_request.reviewed_at = timezone.now()
    leave_request.review_note = note
    leave_request.updated_by = declined_by
    leave_request.save()
    return leave_request


@transaction.atomic
def cancel_request(leave_request: LeaveRequest, cancelled_by) -> LeaveRequest:
    """Self-service withdrawal — only while still Pending, only by the owner (enforced in the view)."""
    if not leave_request.is_pending:
        raise ValidationError("Only pending requests can be cancelled.")

    leave_request.status = LeaveRequestStatus.CANCELLED
    leave_request.reviewed_by = cancelled_by
    leave_request.reviewed_at = timezone.now()
    leave_request.updated_by = cancelled_by
    leave_request.save()
    return leave_request
