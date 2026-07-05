"""
organization/services.py

Business logic for staff deployment / posting.

Deployment history is immutable: redeploying a staff member never
edits or deletes their previous StaffDeployment row. It closes the
row (is_current=False, end_date=<new start date>) and opens a new
one. This mirrors the project-wide rule that operational history is
never overwritten — the exact same pattern used elsewhere in the
project for promotions, transfers and suspensions.

Everything runs inside a single DB transaction with select_for_update
so two admins deploying the same staff member at the same moment
can't both succeed and leave two "current" rows behind (the DB
constraint on the model is the last line of defence if that ever
happens anyway).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction

from employees.models import Staff

from .models import Company, Department, StaffDeployment, StaffRole

User = get_user_model()


@dataclass
class DeploymentResult:
    deployment: StaffDeployment
    previous_deployment: Optional[StaffDeployment]


@transaction.atomic
def deploy_staff(
    *,
    staff: Staff,
    company: Company,
    department: Department,
    designation: StaffRole,
    start_date: date,
    performed_by: Optional[User] = None,
) -> DeploymentResult:
    """
    Deploy (or redeploy) a staff member to a client organization.

    If the staff member already has a current deployment, it is
    closed as of `start_date` and a new deployment is opened. Both
    rows persist — nothing is deleted or overwritten.
    """
    if start_date < staff.date_employed:
        raise ValidationError(
            "Deployment start date cannot be earlier than the staff "
            "member's employment date."
        )

    previous = (
        StaffDeployment.objects.select_for_update()
        .filter(staff=staff, is_current=True)
        .first()
    )

    if previous:
        if start_date <= previous.start_date:
            raise ValidationError(
                "New deployment must start after the current "
                "deployment's start date."
            )
        previous.is_current = False
        previous.end_date = start_date
        previous.updated_by = performed_by
        previous.save(update_fields=["is_current", "end_date", "updated_by", "updated_at"])

    new_deployment = StaffDeployment.objects.create(
        staff=staff,
        company=company,
        department=department,
        designation=designation,
        start_date=start_date,
        is_current=True,
        created_by=performed_by,
        updated_by=performed_by,
    )

    return DeploymentResult(deployment=new_deployment, previous_deployment=previous)


@transaction.atomic
def end_deployment(
    *,
    deployment: StaffDeployment,
    end_date: date,
    performed_by: Optional[User] = None,
) -> StaffDeployment:
    """
    Ends a current deployment without opening a new one — e.g. a
    staff member is pulled off a client site and not yet redeployed
    elsewhere. The row is kept, just marked closed.
    """
    if not deployment.is_current:
        raise ValidationError("This deployment has already ended.")
    if end_date < deployment.start_date:
        raise ValidationError("End date cannot be before the start date.")

    deployment.is_current = False
    deployment.end_date = end_date
    deployment.updated_by = performed_by
    deployment.save(update_fields=["is_current", "end_date", "updated_by", "updated_at"])
    return deployment
