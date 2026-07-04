"""
idcards/signals.py
───────────────────────────────────────────────────────────────────────────
This is the mechanism that makes ID card generation "automatic".

The moment a new Staff row is INSERTed (StaffCreateView in employees/views.py
calls profile_form.save()), Django fires post_save with created=True, and
we issue the card in the same request — the HR officer who just registered
the staff member can click straight through to "View ID Card".

Runs only on creation. Editing a staff profile afterwards does NOT touch
the card (photo/status changes go through IDCardService.reissue_card /
revoke_card explicitly, so the card's own history stays meaningful).
───────────────────────────────────────────────────────────────────────────
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from employees.models import Staff

from .services import IDCardService


@receiver(post_save, sender=Staff, dispatch_uid="idcards_auto_issue_on_staff_create")
def auto_issue_id_card(sender, instance: Staff, created: bool, **kwargs):
    if not created:
        return
    IDCardService.issue_card(staff=instance, issued_by=instance.created_by)
