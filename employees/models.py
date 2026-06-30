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



    
# # Staff Module
# class Organization(models.Model):
#     name = models.CharField(max_length=100, unique=True)
#     description = models.TextField(max_length=200, blank=True)
#     slug = models.SlugField(null=True, blank=True, help_text='Do not enter anything here')

#     def __str__(self):
#         return self.name

#     def save(self, *args, **kwargs):
#         self.slug = slugify(self.name)
#         super().save(*args, **kwargs)

#     class Meta:
#         verbose_name = 'Organization '
#         verbose_name_plural = 'Organization'


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




# Staff Module
class Staff(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    first_name = models.CharField(max_length=20, blank=True, null=True)
    middle_name = models.CharField(max_length=20, blank=True, null=True)
    last_name = models.CharField(max_length=20, blank=True, null=True)
    
    female = 'female'
    male = 'male'
    select_gender = 'select_gender'

    gender_type = [
        ('female', female),
        ('male', male),
        ('select_gender', select_gender),
    ]

    gender= models.CharField(max_length=20, choices=gender_type, default= select_gender)
    DOB = models.DateField(default='1998-01-01')

    select = 'Select'
    abia = 'Abia'
    adamawa = 'Adamawa'
    akwa_ibom = 'Akwa_Ibom'
    anambra = 'Anambra'
    bauchi = 'Bauchi'
    bayelsa = 'Bayelsa'
    benue = 'Benue'
    borno = 'Borno'
    cross_river = 'Cross_river'
    delta = 'Delta'
    ebonyi = 'Ebonyi'
    edo = 'Edo'
    ekiti = 'Ekiti'
    enugu = 'Enugu'
    fct_abuja = 'Fct_abuja'
    gombe = 'Gombe'
    imo = 'Imo'
    jigawa = 'Jigawa'
    kaduna = 'Kaduna'
    kano = 'Kano'
    katsina = 'Katsina'
    kebbi = 'Kebbi'
    kogi = 'Kogi'
    kwara = 'Kwara'
    lagos = 'Lagos'
    nasarawa = 'Nasarawa'
    niger = 'Niger'
    ogun = 'Ogun'
    ondo = 'Ondo'
    osun = 'Osun'
    oyo = 'Oyo'
    plateau = 'Plateau'
    rivers = 'Rivers'
    sokoto = 'Sokoto'
    taraba = 'Taraba'
    yobe = 'Yobe'
    zamfara = 'Zamfara'
    
    states = [
        ('Select', select),
        ('Abia', abia),
        ('Adamawa', adamawa),
        ('Akwa_ibom', akwa_ibom),
        ('Anambra', anambra),
        ('Bauchi', bauchi),
        ('Bayelsa', bayelsa),
        ('Benue', benue),
        ('Borno', borno),
        ('Cross_river', cross_river),
        ('Delta', delta),
        ('Ebonyi', ebonyi),
        ('Edo', edo),
        ('Ekiti', ekiti),
        ('Enugu', enugu),
        ('Fct_abuja', fct_abuja),
        ('Gombe', gombe),
        ('Imo', imo),
        ('Jigawa', jigawa),
        ('Kaduna', kaduna),
        ('Katsina', katsina),
        ('Kebbi', kebbi),
        ('Kogi', kogi),
        ('Kwara', kwara),
        ('Lagos', lagos),
        ('Nasarawa', nasarawa),
        ('Niger', niger),
        ('Ogun', ogun),
        ('Ondo', ondo),
        ('Osun', osun),
        ('Oyo', oyo),
        ('Plateau', plateau),
        ('Rivers', rivers),
        ('Sokoto', sokoto),
        ('Taraba', taraba),
        ('Yobe', yobe),
        ('Zamfara', zamfara),
        
    ]
    
    state_of_origin = models.CharField(max_length=15, choices=states, default=select)    
    
    married = 'married'
    single = 'single'
    select = 'select'

    marital_status = [
        (married, 'married'),
        (single, 'single'),
        (select, 'select'),
    ]

    marital_status = models.CharField(max_length=15, choices=marital_status, default=select)

    # Employment Info
    staff_rank = models.ForeignKey(StaffRank, on_delete=models.CASCADE, default=1, related_name='my_dept', blank=True, null=True)
    organization_assigned = models.ManyToManyField(Organization, related_name='employees')
    role_assigned = models.ManyToManyField(StaffRole, blank=True, related_name='employees')
    dept_assigned = models.ManyToManyField(Department, blank=True, related_name='employees')    
    date_employed = models.DateField(default='1998-01-01')

    # Personal Contact Info
    phone_home = models.CharField(max_length=11, null=True, blank=True)
    phone_mobile = models.CharField(max_length=11, null=True, blank=True)
    address_line1 = models.CharField(max_length=150, blank=True, null=True)
    address_line1 = models.CharField(max_length=150, blank=True, null=True)    
    

    # Academic information
    qualification = models.CharField(max_length=150, default='OND')
    year = models.DateField(default='1998-01-01')
    institution = models.CharField(max_length=150, blank=True)
    professional_body = models.CharField(max_length=150, blank=True)

    # Guarantor's information
    guarantor_name = models.CharField(max_length=150, blank=True)
    guarantor_phone = models.CharField(max_length=15, blank=True)
    guarantor_address = models.CharField(max_length=150, blank=True)
    guarantor_email = models.CharField(max_length=60, blank=True)

    # next of kin info
    next_of_kin_name = models.CharField(max_length=60, blank=True)
    next_of_kin_address = models.CharField(max_length=150, blank=True)
    next_of_kin_phone = models.CharField(max_length=15, blank=True)

    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=False, blank=True)


    def __str__(self):
        return f'{self.first_name} - {self.last_name}'


    def get_full_name(self):

        names = [self.user.last_name, self.user.first_name, self.middle_name]
        full_name = " ".join(filter(None, names))
        return full_name.strip()


    class Meta:
        ordering = ['last_name']

        verbose_name = 'Staff Details'
        verbose_name_plural = 'Staff Details'



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