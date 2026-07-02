import uuid

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

from .payroll_period import PayrollPeriod
from .choices import PaymentBatchStatus
from django.db.models import Sum



class PayrollPaymentBatch(models.Model):
    """
    Groups many payroll payments into
    a single bank payment transaction.

    Example

    January Salary Batch

    contains

    350 Payroll Payments

    exported to GTBank.

    """
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )

    batch_number = models.CharField(
        max_length=30,
        unique=True,
    )

    payroll_period = models.ForeignKey(
        PayrollPeriod,
        on_delete=models.PROTECT,
        related_name="payment_batches",
    )

    batch_name = models.CharField(
        max_length=150,
    )

    bank_name = models.CharField(
        max_length=120,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=PaymentBatchStatus.choices,
        default=PaymentBatchStatus.OPEN,
    )

    total_staff = models.PositiveIntegerField(
        default=0,
    )

    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
    )

    exported = models.BooleanField(
        default=False,
    )

    exported_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    approved = models.BooleanField(
        default=False,
    )

    approved_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="approved_payment_batches",
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    remarks = models.TextField(
        blank=True,
    )

    created_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_payment_batches",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:

        ordering = [
            "-created_at",
        ]

        verbose_name = "Payroll Payment Batch"

        verbose_name_plural = "Payroll Payment Batches"

        indexes = [

            models.Index(fields=["batch_number"]),

            models.Index(fields=["status"]),

            models.Index(fields=["payroll_period"]),

        ]

    def __str__(self):
        return self.batch_name

    def update_totals(self):
        """
        Recalculate the batch totals from all linked
        payroll payments.

        Only successful (PAID) or pending payments
        are included. Reversed and cancelled payments
        are excluded.
        """

        from .choices import PaymentStatus

        payments = self.payments.exclude(
            status__in=[
                PaymentStatus.REVERSED,
                PaymentStatus.CANCELLED,
            ]
        )

        self.total_staff = payments.count()

        self.total_amount = (
            payments.aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

        self.save(
            update_fields=[
                "total_staff",
                "total_amount",
            ]
        )


    def save(self, *args, **kwargs):

        if not self.batch_number:

            year = timezone.now().year

            last = PayrollPaymentBatch.objects.order_by("-id").first()

            next_no = 1

            if last:

                next_no = last.id + 1

            self.batch_number = (
                f"PAY-{year}-{next_no:05d}"
            )

        super().save(*args, **kwargs)


    def approve(self, user):

        self.approved = True

        self.approved_by = user

        self.approved_at = timezone.now()

        self.status = PaymentBatchStatus.PROCESSING

        self.save()


    def complete(self):

        self.status = PaymentBatchStatus.COMPLETED

        self.save()


    def cancel(self):

        self.status = PaymentBatchStatus.CANCELLED

        self.save()


    def mark_exported(self):

        self.exported = True

        self.exported_at = timezone.now()

        self.save()