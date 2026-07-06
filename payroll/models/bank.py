from core.models import AuditableModel
from django.db import models

from employees.models import Staff


class StaffBankAccount(AuditableModel):
    """
    A staff member's salary payment bank account.

    Kept as its own model (one-to-one with Staff — payroll only ever
    pays into ONE primary account at a time) so HR can update bank
    details without touching payroll history: BankScheduleItem
    snapshots these fields at generation time, so a past bank
    schedule never changes even if the staff member updates their
    account afterwards.
    """

    staff = models.OneToOneField(Staff, on_delete=models.CASCADE, related_name="bank_account")

    bank_name = models.CharField(max_length=100)
    bank_code = models.CharField(
        max_length=10, blank=True, help_text="CBN bank sort/routing code, if known."
    )
    account_name = models.CharField(max_length=150)
    account_number = models.CharField(max_length=20)
    bvn = models.CharField(max_length=11, blank=True, help_text="Bank Verification Number.")

    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Staff Bank Account"
        verbose_name_plural = "Staff Bank Accounts"
        indexes = [models.Index(fields=["account_number"])]

    def __str__(self):
        return f"{self.staff.full_name} - {self.bank_name} ({self.account_number})"
