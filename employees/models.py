import uuid

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from employees.core.choices import NigerianState

from organization.models import StaffRank


class Gender(models.TextChoices):
    MALE = "Male", "Male"
    FEMALE = "Female", "Female"


class MaritalStatus(models.TextChoices):
    SINGLE = "Single", "Single"
    MARRIED = "Married", "Married"
    DIVORCED = "Divorced", "Divorced"
    WIDOWED = "Widowed", "Widowed"


class EmploymentType(models.TextChoices):
    PERMANENT = "Permanent", "Permanent"
    CONTRACT = "Contract", "Contract"
    TEMPORARY = "Temporary", "Temporary"
    CASUAL = "Casual", "Casual"
    INTERN = "Intern", "Intern"
    NYSC = "NYSC", "NYSC"
    PROBATION = "Probation", "Probation"


class EmploymentStatus(models.TextChoices):
    ACTIVE = "Active", "Active"
    ON_LEAVE = "On Leave", "On Leave"
    SUSPENDED = "Suspended", "Suspended"
    RESIGNED = "Resigned", "Resigned"
    TERMINATED = "Terminated", "Terminated"
    RETIRED = "Retired", "Retired"


class Staff(models.Model):
    """
    Core Employee Record.

    Company assignment, department, role and branch
    are maintained through the StaffDeployment model.
    Payroll, leave, attendance, documents and loans
    are handled by their respective apps.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="staff_profile",
    )

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )

    employee_no = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        blank=True,
        help_text="Automatically generated employee number",
    )

    middle_name = models.CharField(
        max_length=50,
        blank=True,
    )

    gender = models.CharField(
        max_length=10,
        choices=Gender.choices,
        default=Gender.MALE,
    )

    date_of_birth = models.DateField()

    state_of_origin = models.CharField(
    max_length=30,
    choices=NigerianState.choices,
    default=NigerianState.SELECT,
)
    nationality = models.CharField(
        max_length=50,
        default="Nigeria",
    )

    marital_status = models.CharField(
        max_length=20,
        choices=MaritalStatus.choices,
        default=MaritalStatus.SINGLE,
    )

    employment_type = models.CharField(
        max_length=20,
        choices=EmploymentType.choices,
        default=EmploymentType.PERMANENT,
    )

    employment_status = models.CharField(
        max_length=20,
        choices=EmploymentStatus.choices,
        default=EmploymentStatus.ACTIVE,
    )

    staff_rank = models.ForeignKey(
        StaffRank,
        on_delete=models.PROTECT,
        related_name="employees",
        blank=True,
        null=True,
    )

    date_employed = models.DateField()

    confirmation_date = models.DateField(
        blank=True,
        null=True,
    )

    phone_mobile = models.CharField(
        max_length=20,
        blank=True,
    )

    phone_home = models.CharField(
        max_length=20,
        blank=True,
    )

    official_email = models.EmailField(
        blank=True,
    )

    personal_email = models.EmailField(
        blank=True,
    )

    address = models.CharField(
        max_length=255,
        blank=True,
    )

    qualification = models.CharField(
        max_length=150,
        blank=True,
    )

    graduation_year = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
    )

    institution = models.CharField(
        max_length=150,
        blank=True,
    )

    professional_body = models.CharField(
        max_length=150,
        blank=True,
    )

    guarantor_name = models.CharField(
        max_length=150,
        blank=True,
    )

    guarantor_phone = models.CharField(
        max_length=20,
        blank=True,
    )

    guarantor_email = models.EmailField(
        blank=True,
    )

    guarantor_address = models.CharField(
        max_length=255,
        blank=True,
    )

    next_of_kin_name = models.CharField(
        max_length=150,
        blank=True,
    )

    next_of_kin_phone = models.CharField(
        max_length=20,
        blank=True,
    )

    next_of_kin_address = models.CharField(
        max_length=255,
        blank=True,
    )

    notes = models.TextField(
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created = models.DateTimeField(
        auto_now_add=True,
    )

    updated = models.DateTimeField(
        auto_now=True,
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="staff_created",
        null=True,
        blank=True,
    )

    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="staff_updated",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = (
            "user__last_name",
            "user__first_name",
        )
        verbose_name = "Staff"
        verbose_name_plural = "Staff"

        indexes = [
            models.Index(fields=["employee_no"]),
            models.Index(fields=["employment_status"]),
            models.Index(fields=["date_employed"]),
        ]

    def __str__(self):
        return f"{self.employee_no} - {self.user.get_full_name()}"

    def save(self, *args, **kwargs):
        if not self.employee_no:
            last = Staff.objects.order_by("-id").first()
            number = 1 if last is None else last.id + 1
            self.employee_no = f"EMP{number:05d}"

        super().save(*args, **kwargs)

    @property
    def full_name(self):
        return " ".join(
            filter(
                None,
                [
                    self.user.last_name,
                    self.user.first_name,
                    self.middle_name,
                ],
            )
        )

    @property
    def age(self):
        today = timezone.localdate()
        return (
            today.year
            - self.date_of_birth.year
            - (
                (today.month, today.day)
                < (
                    self.date_of_birth.month,
                    self.date_of_birth.day,
                )
            )
        )

    @property
    def current_deployment(self):
        """
        Returns the employee's active deployment.
        """
        return (
            self.deployments.select_related(
                "company",
                "department",
                "branch",
                "role",
            )
            .filter(is_current=True)
            .first()
        )
# Staff Attendance

class StaffAttendance(models.Model):

    STATUS_CHOICES = (
        ('present', 'Present'),
        ('late', 'Late'),
        ('excused', 'Excused'),
        ('half_day', 'Half Day'),
    )

    employee = models.ForeignKey(
        'Staff',
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )

    date = models.DateField(
        default=timezone.localdate
    )

    check_in_time = models.TimeField(
        null=True,
        blank=True
    )

    check_out_time = models.TimeField(
        null=True,
        blank=True
    )

    checked_in_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='staff_checked_in'
    )

    checked_out_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='staff_checked_out'
    )

    is_late = models.BooleanField(
        default=False
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='present'
    )

    remarks = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        unique_together = ('employee', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.employee} - {self.date}"

    @property
    def work_duration(self):
        """
        Returns formatted work duration (e.g. 6 hrs 30 mins)
        """

        if self.check_in_time and self.check_out_time:

            start = datetime.combine(
                self.date,
                self.check_in_time
            )

            end = datetime.combine(
                self.date,
                self.check_out_time
            )

            duration = end - start

            total_seconds = duration.total_seconds()

            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60

            return f"{int(hours)} hrs {int(minutes)} mins"

        return "N/A"