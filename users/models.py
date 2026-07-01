import uuid

from django.contrib.auth.models import User
from django.db import models

from users.utils import generate_ref_code
from employees.core.choices import NigerianState


class UserType(models.TextChoices):
    ADMIN = "Admin", "Administrator"
    HR = "HR", "Human Resource"
    PAYROLL = "Payroll", "Payroll Officer"
    ACCOUNTANT = "Accountant", "Accountant"
    STAFF = "Staff", "Staff"
    CLIENT = "Client", "Client"
    SUPERVISOR = "Supervisor", "Supervisor"
    AUDITOR = "Auditor", "Auditor"


class Profile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
    )

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )

    image = models.ImageField(
        upload_to="profile_pics",
        default="default.jpg",
        blank=True,
        null=True,
        verbose_name="Profile Picture",
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
    )

    state_of_origin = models.CharField(
        max_length=30,
        choices=NigerianState.choices,
        default=NigerianState.SELECT,
    )

    address = models.CharField(
        max_length=255,
        blank=True,
    )

    bio = models.TextField(
        blank=True,
    )

    user_type = models.CharField(
        max_length=20,
        choices=UserType.choices,
        default=UserType.STAFF,
    )

    referral_code = models.CharField(
        max_length=10,
        blank=True,
        unique=True,
    )

    recommended_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recommended_profiles",
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

    class Meta:
        ordering = (
            "user__last_name",
            "user__first_name",
        )

        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def __str__(self):

        return self.full_name

    @property
    def full_name(self):

        return self.user.get_full_name() or self.user.username

    @property
    def image_url(self):

        if self.image:
            return self.image.url

        return "/static/pages/images/default.jpg"

    def get_recommended_profiles(self):

        return Profile.objects.filter(
            recommended_by=self.user
        )

    def save(self, *args, **kwargs):

        if not self.referral_code:
            self.referral_code = generate_ref_code()

        super().save(*args, **kwargs)