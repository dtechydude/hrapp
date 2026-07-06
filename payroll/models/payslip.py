import hashlib
import uuid

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from .payroll import Payroll


class Payslip(models.Model):
    """
    Official employee payslip.

    A payslip is generated from a completed payroll.

    It is a permanent payroll document and should never
    be deleted.

    The PDF generated is stored permanently so that
    employees can download exactly the same payslip
    years later.
    """

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )

    payroll = models.OneToOneField(
        Payroll,
        on_delete=models.PROTECT,
        related_name="payslip",
    )

    payslip_number = models.CharField(
        max_length=30,
        unique=True,
        editable=False,
    )

    pdf = models.FileField(
        upload_to="payroll/payslips/%Y/%m/",
        blank=True,
        null=True,
        help_text="Generated PDF copy of the payslip.",
    )

    verification_token = models.CharField(
        max_length=64,
        unique=True,
        editable=False,
        help_text="Used to verify authenticity of the payslip.",
    )

    qr_code = models.ImageField(
        upload_to="payroll/payslip_qr/",
        blank=True,
        null=True,
        help_text="Optional QR Code for online verification.",
    )

    emailed = models.BooleanField(
        default=False,
    )

    emailed_to = models.EmailField(
        blank=True,
    )

    emailed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    download_count = models.PositiveIntegerField(
        default=0,
    )

    print_count = models.PositiveIntegerField(
        default=0,
    )

    last_downloaded_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    last_printed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    acknowledged = models.BooleanField(
        default=False,
        help_text="Employee acknowledged receipt of payslip.",
    )

    acknowledged_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    generated_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="generated_payslips",
    )

    generated_at = models.DateTimeField(
        auto_now_add=True,
    )

    remarks = models.TextField(
        blank=True,
    )

    class Meta:

        ordering = [
            "-generated_at",
        ]

        verbose_name = "Payslip"

        verbose_name_plural = "Payslips"

        indexes = [

            models.Index(fields=["payslip_number"]),

            models.Index(fields=["generated_at"]),

            models.Index(fields=["verification_token"]),

        ]

    def __str__(self):
        return (
            f"{self.payslip_number} - "
            f"{self.payroll.staff.full_name}"
        )

    def save(self, *args, **kwargs):

        creating = self.pk is None

        if creating:

            period = self.payroll.payroll_period

            last = Payslip.objects.order_by("-id").first()

            next_number = 1 if not last else last.id + 1

            self.payslip_number = (
                f"PS-"
                f"{period.year}-"
                f"{period.month:02d}-"
                f"{next_number:06d}"
            )

        if not self.verification_token:

            self.verification_token = hashlib.sha256(

                (
                    str(self.payroll.uuid)
                    + str(timezone.now().timestamp())

                ).encode()

            ).hexdigest()

        self.full_clean()

        super().save(*args, **kwargs)

    @property
    def employee(self):
        return self.payroll.staff

    @property
    def payroll_period(self):
        return self.payroll.payroll_period

    @property
    def gross_salary(self):
        return self.payroll.gross_salary

    @property
    def total_earnings(self):
        return self.payroll.total_earnings

    @property
    def total_deductions(self):
        return self.payroll.total_deductions

    @property
    def net_salary(self):
        return self.payroll.net_salary

    @property
    def payment_status(self):
        return self.payroll.payment_status

    @property
    def payment_date(self):
        return self.payroll.payment_date

    def record_download(self):

        self.download_count += 1

        self.last_downloaded_at = timezone.now()

        self.save(
            update_fields=[
                "download_count",
                "last_downloaded_at",
            ]
        )

    def record_print(self):

        self.print_count += 1

        self.last_printed_at = timezone.now()

        self.save(
            update_fields=[
                "print_count",
                "last_printed_at",
            ]
        )

    def mark_emailed(self, email):

        self.emailed = True

        self.emailed_to = email

        self.emailed_at = timezone.now()

        self.save(
            update_fields=[
                "emailed",
                "emailed_to",
                "emailed_at",
            ]
        )

    def acknowledge(self):

        self.acknowledged = True

        self.acknowledged_at = timezone.now()

        self.save(
            update_fields=[
                "acknowledged",
                "acknowledged_at",
            ]
        )

    def verify(self, token):

        return self.verification_token == token