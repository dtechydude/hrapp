import uuid

from decimal import Decimal

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone

from .payroll import Payroll
from .choices import (
    PaymentMethod,
    PaymentStatus,
    PaymentChannel,
    PaymentBatchStatus,
)


class PayrollPayment(models.Model):
    """
    Stores actual salary payment transactions.

    A payroll can have multiple payments
    (partial payments).

    Financial records must never be deleted.
    """

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )

    payroll = models.ForeignKey(
        Payroll,
        on_delete=models.PROTECT,
        related_name="payments",
    )

    payment_batch = models.ForeignKey(
        "PayrollPaymentBatch",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
    )

    payment_reference = models.CharField(
        max_length=120,
        unique=True,
    )

    payment_method = models.CharField(
        max_length=30,
        choices=PaymentMethod.choices,
    )

    payment_channel = models.CharField(
        max_length=30,
        choices=PaymentChannel.choices,
        default=PaymentChannel.MANUAL,
    )

    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )

    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    payment_date = models.DateTimeField(
        default=timezone.now,
    )

    narration = models.CharField(
        max_length=255,
        blank=True,
    )

    bank_name = models.CharField(
        max_length=150,
        blank=True,
    )

    account_name = models.CharField(
        max_length=150,
        blank=True,
    )

    account_number = models.CharField(
        max_length=20,
        blank=True,
    )

    transaction_reference = models.CharField(
        max_length=120,
        blank=True,
    )

    gateway_response = models.TextField(
        blank=True,
    )

    remarks = models.TextField(
        blank=True,
    )

    processed_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="payroll_payments_processed",
    )

    verified_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="payroll_payments_verified",
    )

    verified_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        ordering = [
            "-payment_date",
        ]

        verbose_name = "Payroll Payment"

        verbose_name_plural = "Payroll Payments"

        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["payment_date"]),
            models.Index(fields=["payment_reference"]),
        ]

    def __str__(self):
        return (
            f"{self.payroll.staff.full_name}"
            f" - ₦{self.amount}"
            )


    def clean(self):

        super().clean()

        if self.amount <= 0:
            raise ValidationError(
                {
                    "amount":
                    "Payment amount must be greater than zero."
                }
            )

        if self.amount > self.payroll.net_salary:
            raise ValidationError(
                {
                    "amount":
                    "Payment exceeds employee net salary."
                }
            )

        if (
            self.payment_batch
            and self.payment_batch.status
            == PaymentBatchStatus.COMPLETED
        ):
            raise ValidationError(
                "Cannot modify a completed payment batch."
            )


    def save(self, *args, **kwargs):

        self.full_clean()

        old_batch = None

        if self.pk:
            old_batch = (
                PayrollPayment.objects
                .filter(pk=self.pk)
                .values_list("payment_batch", flat=True)
                .first()
            )

        super().save(*args, **kwargs)

        if old_batch and (
            not self.payment_batch
            or old_batch != self.payment_batch.id
        ):
            from .payroll_payment_batch import PayrollPaymentBatch

            try:
                PayrollPaymentBatch.objects.get(
                    pk=old_batch
                ).update_totals()
            except PayrollPaymentBatch.DoesNotExist:
                pass

        if self.payment_batch:
            self.payment_batch.update_totals()


    def delete(self, *args, **kwargs):

        batch = self.payment_batch

        super().delete(*args, **kwargs)

        if batch:
            batch.update_totals()


    @property
    def is_paid(self):
        return self.status == PaymentStatus.PAID


    @property
    def is_pending(self):
        return self.status == PaymentStatus.PENDING


    @property
    def is_failed(self):
        return self.status == PaymentStatus.FAILED


    @property
    def remaining_balance(self):

        paid = self.payroll.payments.filter(
            status=PaymentStatus.PAID
        ).exclude(
            pk=self.pk
        ).aggregate(
            models.Sum("amount")
        )["amount__sum"] or Decimal("0.00")

        return self.payroll.net_salary - (
            paid + self.amount
        )

    def mark_as_paid(
        self,
        verified_by=None,
        transaction_reference=None,
    ):

        self.status = PaymentStatus.PAID

        self.verified_by = verified_by

        self.verified_at = timezone.now()

        if transaction_reference:
            self.transaction_reference = transaction_reference

        self.save()


    def reverse(self):

        if self.status != PaymentStatus.PAID:
            raise ValidationError(
                "Only paid transactions can be reversed."
            )

        self.status = PaymentStatus.REVERSED

        self.save()