"""
core/models.py

Project-wide abstract base classes. Nothing in this file is a concrete
table on its own — every class here has `abstract = True` and exists
purely so every app (organization, employees, payroll, loans, leave,
accounting, documents, ...) gets identical audit-trail behaviour
without copy-pasting the same five fields into every model.

Usage:
    from core.models import AuditableModel

    class Company(AuditableModel):
        name = models.CharField(max_length=100)
        ...
"""
from django.conf import settings
from django.db import models


class AuditableModel(models.Model):
    """
    Provides the standard audit columns required project-wide:
    is_active, created_at, updated_at, created_by, updated_by.

    `created_by` / `updated_by` use related_name="+" deliberately —
    dozens of unrelated models (Company, Department, StaffDeployment,
    future Payroll/Loan/Leave records, ...) all inherit this class, so
    a fixed related_name would collide across every one of them on
    the User model. "+" tells Django not to create a reverse relation
    at all, which is the correct choice here since "all objects this
    user has ever touched" isn't a query this project needs — audit
    reads go through the AuditLog app instead (see the `audit` app).

    Soft delete convention: `is_active=False` marks a record retired
    without a hard DELETE, matching the project rule that operational
    history is never destroyed. Querysets that should hide retired
    records are responsible for filtering `is_active=True` themselves
    (or via a manager) — this base class only stores the flag.
    """

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

    class Meta:
        abstract = True