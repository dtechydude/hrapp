import uuid as uuid_lib
from datetime import timedelta

from django.core.validators import FileExtensionValidator
from django.db import models
from django.template.defaultfilters import slugify
from django.utils import timezone

from core.models import AuditableModel
from core.validators import IMAGE_EXTENSIONS, validate_file_size

from .managers import StaffDeploymentManager


def company_logo_upload_path(instance: "Company", filename: str) -> str:
    """
    UUID-based filename — never trust a user-supplied filename for
    the on-disk path (secure file upload requirement). Bucketed by
    company code once the row has one; falls back to 'pending' for a
    brand-new, not-yet-saved Company during initial form submission.
    """
    ext = filename.rsplit(".", 1)[-1].lower()
    bucket = instance.code or "pending"
    return f"organizations/logos/{bucket}/{uuid_lib.uuid4()}.{ext}"


class OrganizationStatus(models.TextChoices):
    ACTIVE = "Active", "Active"
    INACTIVE = "Inactive", "Inactive"
    SUSPENDED = "Suspended", "Suspended"
    CONTRACT_ENDED = "Contract Ended", "Contract Ended"


class Company(AuditableModel):
    """
    A client organization the outsourcing company deploys staff to.

    One Company has many Staff, via StaffDeployment (see
    Staff.current_deployment / StaffDeployment.company below).
    """

    name = models.CharField(max_length=100, unique=True)

    code = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        blank=True,
        help_text="Automatically generated if left blank (e.g. ORG0001).",
    )

    industry = models.CharField(max_length=100, blank=True)

    description = models.TextField(max_length=200, blank=True)

    address = models.CharField(
        max_length=255,
        blank=True,
        help_text="Physical address — shown as a staff member's deployment location.",
    )

    contact_person = models.CharField(max_length=150, blank=True)

    phone = models.CharField(max_length=20, blank=True)

    email = models.EmailField(blank=True)

    contract_start_date = models.DateField(null=True, blank=True)

    contract_end_date = models.DateField(null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=OrganizationStatus.choices,
        default=OrganizationStatus.ACTIVE,
    )

    logo = models.ImageField(
        upload_to=company_logo_upload_path,
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(IMAGE_EXTENSIONS),
            validate_file_size,
        ],
        help_text="Displayed on printable reports and client-facing pages.",
    )

    notes = models.TextField(blank=True)

    slug = models.SlugField(null=True, blank=True, help_text="Do not enter anything here")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        if not self.code:
            last = Company.objects.order_by("-id").first()
            number = 1 if last is None else last.id + 1
            self.code = f"ORG{number:04d}"
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"

    @property
    def is_contract_expiring_soon(self) -> bool:
        """Feeds the 'Upcoming Contract Expiry' dashboard notification."""
        if not self.contract_end_date:
            return False
        return self.contract_end_date <= timezone.localdate() + timedelta(days=30)


class Department(AuditableModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(max_length=200, blank=True)
    slug = models.SlugField(null=True, blank=True, help_text="Do not enter anything here")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Department"
        verbose_name_plural = "Departments"


class StaffRole(AuditableModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(max_length=200, blank=True)
    slug = models.SlugField(null=True, blank=True, help_text="Do not enter anything here")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Employee Role"
        verbose_name_plural = "Employee Role"


class StaffRank(AuditableModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(max_length=200, blank=True)
    slug = models.SlugField(null=True, blank=True, help_text="Do not enter anything here")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Employee Rank"
        verbose_name_plural = "Employee Rank"


class StaffDeployment(AuditableModel):
    """
    A single posting of a staff member to a client organization.

    Redeploying a staff member NEVER edits this row once it exists as
    a closed record — see organization.services.deploy_staff(). The
    only mutation ever applied to an already-open row is closing it:
    is_current -> False and end_date set. Nothing is deleted.
    """

    staff = models.ForeignKey(
        "employees.Staff",
        on_delete=models.PROTECT,
        related_name="deployments",
    )

    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        related_name="deployments",
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="deployments",
    )

    designation = models.ForeignKey(
        StaffRole,
        on_delete=models.PROTECT,
        related_name="deployments",
    )

    start_date = models.DateField()

    end_date = models.DateField(blank=True, null=True)

    is_current = models.BooleanField(default=True)

    objects = StaffDeploymentManager()

    class Meta:
        ordering = ["-is_current", "-start_date"]
        indexes = [
            models.Index(fields=["staff", "is_current"]),
            models.Index(fields=["company", "is_current"]),
        ]
        constraints = [
            # A staff member can never have two "current" postings —
            # enforced at the DB level, not just in application code.
            models.UniqueConstraint(
                fields=["staff"],
                condition=models.Q(is_current=True),
                name="unique_current_deployment_per_staff",
            )
        ]

    def __str__(self):
        return f"{self.staff} - {self.company}"

    @property
    def location(self) -> str:
        """Human-readable posting location for display purposes."""
        return self.company.address or self.company.name