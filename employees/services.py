"""
idcards/services.py
───────────────────────────────────────────────────────────────────────────
Business logic for issuing, reissuing, and revoking staff ID cards.

Views and signals call into this layer only — they never touch the model
directly for anything beyond simple reads. This keeps views thin and the
rules in one place, per the project's architecture standard.
───────────────────────────────────────────────────────────────────────────
"""
from django.db import transaction
from django.utils import timezone

from .models import IDCardReissueLog, IDCardStatus, StaffIDCard
from .utils import default_expiry_date, generate_card_number, generate_qr_png


class IDCardService:
    """Namespaced service methods — call as IDCardService.issue_card(...)."""

    # ── Issue (first-time, called by the post_save signal) ──────────
    @staticmethod
    @transaction.atomic
    def issue_card(staff, issued_by=None) -> StaffIDCard:
        """
        Idempotent: safe to call more than once for the same staff member
        (e.g. a legacy record that predates this module) — get_or_create
        guarantees only one card ever exists per staff.
        """
        card, created = StaffIDCard.objects.get_or_create(
            staff=staff,
            defaults={
                "card_number": generate_card_number(staff),
                "issue_date": timezone.localdate(),
                "expiry_date": default_expiry_date(staff),
                "status": IDCardStatus.ACTIVE,
                "created_by": issued_by,
                "updated_by": issued_by,
            },
        )
        if created:
            card.qr_code = generate_qr_png(card.verification_url)
            card.save(update_fields=["qr_code"])
        return card

    # ── Reissue (lost card, photo change, contract renewal, etc.) ───
    @staticmethod
    @transaction.atomic
    def reissue_card(staff, issued_by=None, reason: str = "") -> StaffIDCard:
        card = staff.id_card
        previous_number = card.card_number

        card.card_number = generate_card_number(staff, year=timezone.localdate().year)
        card.issue_date = timezone.localdate()
        card.expiry_date = default_expiry_date(staff)
        card.status = IDCardStatus.ACTIVE
        card.updated_by = issued_by
        card.qr_code = generate_qr_png(card.verification_url)
        card.save()

        IDCardReissueLog.objects.create(
            card=card,
            previous_card_number=previous_number,
            new_card_number=card.card_number,
            reason=reason,
            action="Reissued",
            performed_by=issued_by,
        )
        return card

    # ── Revoke (termination, security incident, etc.) ───────────────
    @staticmethod
    @transaction.atomic
    def revoke_card(staff, revoked_by=None, reason: str = "") -> StaffIDCard:
        card = staff.id_card
        card.status = IDCardStatus.REVOKED
        card.revoked_reason = reason
        card.revoked_at = timezone.now()
        card.revoked_by = revoked_by
        card.updated_by = revoked_by
        card.save()

        IDCardReissueLog.objects.create(
            card=card,
            previous_card_number=card.card_number,
            new_card_number=card.card_number,
            reason=reason,
            action="Revoked",
            performed_by=revoked_by,
        )
        return card
