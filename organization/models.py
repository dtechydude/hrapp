from django.db import models
import math
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
from django.db.models.signals import post_save, post_delete
from datetime import timedelta
from django.template.defaultfilters import slugify
from users.models import Profile
from datetime import datetime
from django.utils import timezone
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import datetime



    
# company Module
class Company(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(max_length=200, blank=True)
    slug = models.SlugField(null=True, blank=True, help_text='Do not enter anything here')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Organization '
        verbose_name_plural = 'Organization'


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(max_length=200, blank=True)
    slug = models.SlugField(null=True, blank=True, help_text='Do not enter anything here')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Employee Rank'
        verbose_name_plural = 'Employee Rank'



class StaffRole(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(max_length=200, blank=True)
    slug = models.SlugField(null=True, blank=True, help_text='Do not enter anything here')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Employee Role'
        verbose_name_plural = 'Employee Role'


class StaffRank(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(max_length=200, blank=True)
    slug = models.SlugField(null=True, blank=True, help_text='Do not enter anything here')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Employee Rank'
        verbose_name_plural = 'Employee Rank'




class StaffDeployment(models.Model):

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

    end_date = models.DateField(
        blank=True,
        null=True
    )

    is_current = models.BooleanField(
        default=True
    )

    class Meta:
        ordering = ["-is_current", "-start_date"]

    def __str__(self):
        return f"{self.staff} - {self.company}"
