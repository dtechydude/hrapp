"""
idcards/utils.py
───────────────────────────────────────────────────────────────────────────
Pure helper functions for the ID card module — no DB writes, no view
logic. Kept separate from services.py so they're trivially unit-testable.

Dependency note
────────────────
Requires `qrcode` and `Pillow`, both pure-Python-friendly and installable
on every hosting tier this project targets (PythonAnywhere free plan,
shared cPanel/Passenger, VPS). No system packages, no Docker, no Redis.

    pip install qrcode[pil]
───────────────────────────────────────────────────────────────────────────
"""
import io

import qrcode
from django.core.files.base import ContentFile
from django.utils import timezone
from typing import Optional


# def generate_card_number(staff, year: int | None = None) -> str:
def generate_card_number(staff, year: Optional[int] = None) -> str:
    """
    Format: ID-<EmployeeNo>-<Year>
    Uniqueness rides on employee_no, which is already unique on Staff.
    """
    year = year or timezone.localdate().year
    return f"ID-{staff.employee_no}-{year}"


def default_expiry_date(staff, years: int = 3):
    """
    Cards are valid for `years` from issue date, but never outlive the
    staff member's current client-organization contract (if deployed) —
    an outsourced staff member's badge shouldn't grant access past the
    date their deployment contract ends.
    """
    issue = timezone.localdate()
    try:
        expiry = issue.replace(year=issue.year + years)
    except ValueError:
        # 29 Feb edge case
        expiry = issue.replace(month=2, day=28, year=issue.year + years)

    deployment = getattr(staff, "current_deployment", None)
    company = getattr(deployment, "company", None) if deployment else None
    contract_end = getattr(company, "contract_end_date", None)
    if contract_end and contract_end < expiry:
        expiry = contract_end

    return expiry


def generate_qr_png(data: str, box_size: int = 8, border: int = 2) -> ContentFile:
    """
    Renders `data` (a verification URL / card payload string) into a QR
    PNG and returns it as a Django ContentFile ready to assign to an
    ImageField, e.g.:

        card.qr_code = generate_qr_png(card.verification_url)
        card.save(update_fields=["qr_code"])
    """
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)
    image = qr.make_image(fill_color="#0B1D3A", back_color="white")

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return ContentFile(buffer.read(), name="qr.png")
