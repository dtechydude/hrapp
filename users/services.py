"""
users/bulk_photo_service.py
───────────────────────────────────────────────────────────────────────────
Independent bulk profile-photo upload service for HRPAMS.

Adapted from a bulk-upload tool built for a different project (a school
management system with separate Student/Teacher/Parent models). That
project's own refactor notes flagged this exact lesson: "Profile.user_type
filter was the wrong approach — query the actual domain model directly,
since a generic flag isn't guaranteed to be kept in sync."

HRPAMS has the same shape of problem: Profile.user_type has a 'Staff'
value, but that flag isn't the authoritative record of who's actually an
employee — employees.Staff is. So the "Employees" bucket below queries
Staff directly (via its OneToOne to User, related_name="staff_profile"),
never Profile.user_type. Every other bucket (Admin, HR, Payroll,
Accountant, Client, Supervisor, Auditor) has no separate domain model,
so those still come from Profile.user_type as before — with accounts
already counted as employees excluded, so nobody appears twice.

This file is intentionally self-contained:
  • Does not modify users/models.py — Profile is used exactly as-is.
  • Does not modify employees/models.py — Staff is read-only here.
  • Does not modify users/views.py or users/urls.py — see
    bulk_photo_views.py and the two-line URL addition in the README.
  • Does not touch your existing single-photo admin upload flow at all.
───────────────────────────────────────────────────────────────────────────
"""
from __future__ import annotations

import logging
import os

from django.contrib.auth import get_user_model
from django.db import transaction

from .models import Profile, UserType

User = get_user_model()
logger = logging.getLogger(__name__)

MAX_SIZE_BYTES = 100 * 1024  # 100 KB — adjust here if your project's limit differs
ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp"}

# The literal default filename set on Profile.image (models.py:
# `default="default.jpg"`). This must NEVER be deleted from disk — it's
# the shared fallback photo for every profile that hasn't uploaded a
# real one yet, not a per-profile file. (The original version of this
# script didn't need this guard because that project's Profile model
# had no shared default file; HRPAMS's does, so deleting on overwrite
# without this check would nuke everyone's fallback photo.)
DEFAULT_IMAGE_NAME = "default.jpg"


# ── Image validation ──────────────────────────────────────────────────────

def _ext(name: str) -> str:
    return os.path.splitext(name.lower())[1]


def validate_single_image(file) -> list[str]:
    errors = []
    if _ext(file.name) not in ALLOWED_EXT:
        errors.append(f'"{file.name}" — unsupported format. Use JPG, PNG or WEBP.')
    if hasattr(file, "content_type") and file.content_type not in ALLOWED_MIME:
        errors.append(f'"{file.name}" — invalid MIME type ({file.content_type}).')
    if file.size > MAX_SIZE_BYTES:
        errors.append(
            f'"{file.name}" — {file.size / 1024:.1f} KB exceeds the '
            f"{MAX_SIZE_BYTES // 1024} KB limit. Please compress the image and retry."
        )
    return errors


# ── Photo helper ────────────────────────────────────────────────────────

def _photo_url(profile: Profile) -> str | None:
    """Safely return the URL of a profile image, or None."""
    try:
        if profile and profile.image:
            return profile.image.url
    except Exception:
        logger.exception(
            "bulk_photo_service: failed to resolve image URL for profile pk=%s",
            getattr(profile, "pk", None),
        )
    return None


def _profile_map(user_ids: list) -> dict:
    """Batch-fetch {user_id: Profile} for a list of user PKs — avoids an
    N+1 query when enriching a list of Staff or Profile rows with photo
    data."""
    return {
        p.user_id: p
        for p in Profile.objects.filter(user_id__in=user_ids)
    }


# ── Category choices for the filter dropdown ──────────────────────────────

def get_category_choices() -> list[tuple[str, str]]:
    """
    'employee' is NOT one of Profile's UserType values — it's a
    dedicated bucket that queries employees.Staff directly (see
    _fetch_employees below). The remaining options are genuine
    account-role flags with no separate domain model, so those still
    come from Profile.user_type — with UserType.STAFF itself excluded
    here so the two paths never overlap or double-count anyone.
    """
    choices = [("employee", "Employees (Staff)")]
    choices += [(value, label) for value, label in UserType.choices if value != UserType.STAFF]
    return choices


# ── Employees — queried directly from employees.Staff ────────────────────

def _fetch_employees() -> list[dict]:
    """
    The authoritative "who is an employee" query: employees.Staff,
    joined to User via its OneToOne (related_name="staff_profile").
    Never uses Profile.user_type — a Staff row existing is the real
    source of truth, not a flag on a different model that could be
    stale or never set.
    """
    try:
        from employees.models import Staff
    except ImportError:
        logger.error("_fetch_employees: cannot import employees.models.Staff")
        return []

    qs = (
        Staff.objects.select_related("user")
        .filter(is_active=True, user__is_active=True)
        .order_by("user__last_name", "user__first_name")
    )

    user_ids = [s.user_id for s in qs]
    profile_map = _profile_map(user_ids)

    results = []
    for staff in qs:
        u = staff.user
        profile = profile_map.get(u.pk)

        deployment = getattr(staff, "current_deployment", None)
        department = getattr(deployment, "department", None) if deployment else None
        label_bits = [str(staff.staff_rank)] if getattr(staff, "staff_rank", None) else [staff.employment_type]
        if department:
            label_bits.append(str(department))
        label = " · ".join(filter(None, label_bits)) or "Employee"

        status = getattr(staff, "employment_status", None) or ("active" if u.is_active else "inactive")

        results.append({
            "user_id": u.pk,
            "username": u.username,
            "usn": staff.employee_no,
            "full_name": staff.full_name,
            "user_type": "employee",
            "label": label,
            "current_photo": _photo_url(profile),
            "status": status.lower() if isinstance(status, str) else status,
        })

    return results


# ── Role accounts — Profile.user_type ─────────────────────────────────────

def _fetch_profiles_by_type(user_type: str) -> list[dict]:
    """
    Admin / HR / Payroll / Accountant / Client / Supervisor / Auditor —
    account-role flags with no separate domain model, so Profile is the
    source here.

    Deliberately does NOT exclude accounts that also have a linked Staff
    record: role and employment status are two different things — an HR
    officer or Payroll officer is very often also an employee with a
    Staff row, and excluding them here would make selecting "HR" or
    "Payroll" return nothing whenever that's true (which is why "All
    Users" was collapsing down to just Employees before this fix — every
    other category was silently filtering itself empty).

    Overlap between this and _fetch_employees() is only resolved where
    it actually matters — combining everything for the "All Users" view,
    in _fetch_all() below — not by hiding data from a specific category.
    """
    qs = Profile.objects.select_related("user").filter(is_active=True, user__is_active=True)

    if user_type != "all":
        qs = qs.filter(user_type=user_type)

    qs = qs.order_by("user__last_name", "user__first_name")

    results = []
    for profile in qs:
        u = profile.user
        results.append({
            "user_id": u.pk,
            "username": u.username,
            "usn": u.username,
            "full_name": u.get_full_name() or u.username,
            "user_type": profile.user_type,
            "label": profile.get_user_type_display(),
            "current_photo": _photo_url(profile),
            "status": "active" if u.is_active else "inactive",
        })

    return results


def _fetch_all() -> list[dict]:
    """Employees + every role-account type, deduplicated by user_id so
    someone who is both (e.g. an HR officer with a Staff record) only
    shows once — as an Employee, since that bucket is checked first."""
    employees = _fetch_employees()
    seen = {row["user_id"] for row in employees}

    others = []
    for value, _label in UserType.choices:
        if value == UserType.STAFF:
            continue
        for row in _fetch_profiles_by_type(value):
            if row["user_id"] not in seen:
                seen.add(row["user_id"])
                others.append(row)

    combined = employees + others
    combined.sort(key=lambda r: r["full_name"].lower())
    return combined


# ── Public entry point ────────────────────────────────────────────────────

def get_profiles_for_type(category: str) -> list[dict]:
    """
    Returns a list of JSON-ready dicts for the photo grid.

    category: 'employee' (queries Staff directly), one of the remaining
    UserType.values (queries Profile, Staff-linked accounts excluded),
    or 'all' for everyone combined.
    """
    if category == "employee":
        return _fetch_employees()
    if category == "all":
        return _fetch_all()
    return _fetch_profiles_by_type(category)


# ── Save photos ────────────────────────────────────────────────────────

def save_bulk_photos(files_map: dict) -> dict:
    """
    Process { 'photo_<user_id>': UploadedFile } from request.FILES.
    Returns { 'saved': int, 'skipped': int, 'errors': list[dict] }
    """
    results = {"saved": 0, "skipped": 0, "errors": []}

    for key, uploaded_file in files_map.items():
        if not key.startswith("photo_"):
            continue

        try:
            user_id = int(key.split("photo_", 1)[1])
        except (ValueError, IndexError):
            continue

        file_errors = validate_single_image(uploaded_file)
        if file_errors:
            try:
                username = User.objects.get(pk=user_id).username
            except User.DoesNotExist:
                username = f"user_{user_id}"
            for err in file_errors:
                results["errors"].append({"user_id": user_id, "username": username, "message": err})
            results["skipped"] += 1
            continue

        try:
            with transaction.atomic():
                try:
                    profile = Profile.objects.select_for_update().get(user_id=user_id)
                except Profile.DoesNotExist:
                    u = User.objects.get(pk=user_id)
                    profile = Profile.objects.create(user=u)
                    logger.info("bulk_photo_service: created missing Profile for user_id=%s", user_id)

                # Remove the OLD image from disk before overwriting — but
                # never delete the shared default.jpg fallback.
                if profile.image and profile.image.name != DEFAULT_IMAGE_NAME:
                    try:
                        old_path = profile.image.path
                        if os.path.isfile(old_path):
                            os.remove(old_path)
                    except Exception:
                        logger.warning(
                            "bulk_photo_service: could not remove old image for user_id=%s", user_id
                        )

                profile.image = uploaded_file
                profile.save(update_fields=["image"])
                results["saved"] += 1

        except User.DoesNotExist:
            results["errors"].append({
                "user_id": user_id,
                "username": f"user_{user_id}",
                "message": f"User with ID {user_id} does not exist.",
            })
            results["skipped"] += 1
        except Exception as e:
            logger.exception("bulk_photo_service: failed for user_id=%s", user_id)
            results["errors"].append({
                "user_id": user_id,
                "username": f"user_{user_id}",
                "message": f"Unexpected error: {e}",
            })
            results["skipped"] += 1

    return results
