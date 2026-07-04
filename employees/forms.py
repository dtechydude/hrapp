from tkinter import Widget
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Staff, StaffAttendance
from django.utils import timezone




# Signup Form For Teachers 
class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ('username', 'first_name', 'last_name', 'email')
    
    # Custom validation to check if username is available
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if get_user_model().objects.filter(username=username).exists():
            raise ValidationError("This username is already taken. Please choose another.")
        return username




"""
employees/forms.py
───────────────────────────────────────────────────────────────────────────
Staff registration / edit forms.

Design decisions
────────────────
• Split into TWO forms rendered together in one view:
    1. StaffUserForm   — Django User fields (first_name, last_name,
                         username, email, password)
    2. StaffProfileForm — Staff model fields, grouped into logical sections
                         via form field ordering and template tabs.

• Both forms are validated together in the view before any DB writes.
• Password is set only on creation; on edit the password section is hidden
  unless the manager explicitly requests a password reset.
• All select/choice fields get a blank "— Select —" prompt.
• Widgets are styled with the HRPAMS CSS design system classes.
───────────────────────────────────────────────────────────────────────────
"""

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Staff, Gender, MaritalStatus, EmploymentType, EmploymentStatus


# ─────────────────────────────────────────────────────────────────────────────
# Shared widget factory helpers
# ─────────────────────────────────────────────────────────────────────────────

def _text(placeholder="", extra_class=""):
    return forms.TextInput(attrs={
        "class": f"form-control {extra_class}".strip(),
        "placeholder": placeholder,
        "autocomplete": "off",
    })


def _email(placeholder=""):
    return forms.EmailInput(attrs={
        "class": "form-control",
        "placeholder": placeholder,
    })


def _select():
    return forms.Select(attrs={"class": "form-control"})


def _date():
    return forms.DateInput(attrs={
        "class": "form-control",
        "type": "date",
    })


def _textarea(rows=3, placeholder=""):
    return forms.Textarea(attrs={
        "class": "form-control",
        "rows": rows,
        "placeholder": placeholder,
    })


def _number(placeholder=""):
    return forms.NumberInput(attrs={
        "class": "form-control",
        "placeholder": placeholder,
    })


def _password():
    return forms.PasswordInput(attrs={
        "class": "form-control",
        "autocomplete": "new-password",
        "placeholder": "Minimum 8 characters",
    })


# ─────────────────────────────────────────────────────────────────────────────
# 1. User Account Form
# ─────────────────────────────────────────────────────────────────────────────

class StaffUserForm(forms.ModelForm):
    """
    Handles the Django auth User portion of staff registration.
    Used for both create (password required) and update (password optional).
    """

    password = forms.CharField(
        label="Password",
        widget=_password(),
        required=False,   # Only required on create; enforced in clean()
        help_text="Leave blank to keep the current password (edit mode only).",
    )

    confirm_password = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "autocomplete": "new-password",
            "placeholder": "Repeat password",
        }),
        required=False,
    )

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "username",
            "email",
        ]
        widgets = {
            "first_name": _text("e.g. Amaka"),
            "last_name":  _text("e.g. Okonkwo"),
            "username":   _text("Login username (auto-suggested)"),
            "email":      _email("official@company.com"),
        }
        labels = {
            "first_name": "First Name",
            "last_name":  "Last Name",
            "username":   "Username",
            "email":      "Login Email",
        }

    def __init__(self, *args, is_create=True, **kwargs):
        self.is_create = is_create
        super().__init__(*args, **kwargs)

        # Make names required
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True

        # Mark password required only on create
        if is_create:
            self.fields["password"].required = True
            self.fields["confirm_password"].required = True
            self.fields["password"].help_text = ""

        # Username: unique check excludes self on update
        if not is_create and self.instance:
            self.fields["username"].help_text = (
                "Changing the username will update the staff's login ID."
            )

    def clean_username(self):
        username = self.cleaned_data.get("username", "").strip()
        qs = User.objects.filter(username__iexact=username)
        if not self.is_create and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(
                "This username is already taken. Please choose another."
            )
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if email:
            qs = User.objects.filter(email__iexact=email)
            if not self.is_create and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(
                    "An account with this email already exists."
                )
        return email

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get("password")
        confirm  = cleaned.get("confirm_password")

        if self.is_create and not password:
            self.add_error("password", "Password is required for new staff.")
            return cleaned

        if password:
            if password != confirm:
                self.add_error("confirm_password", "Passwords do not match.")
            else:
                try:
                    validate_password(password)
                except ValidationError as e:
                    self.add_error("password", e)

        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")
        if password:
            user.set_password(password)
        elif self.is_create:
            # Safety net — should not reach here due to clean()
            user.set_unusable_password()
        if commit:
            user.save()
        return user


# ─────────────────────────────────────────────────────────────────────────────
# 2. Staff Profile Form
# ─────────────────────────────────────────────────────────────────────────────

class StaffProfileForm(forms.ModelForm):
    """
    Handles all Staff model fields.

    Field ordering maps to the four tab sections in the template:
      Tab 1 — Personal Information
      Tab 2 — Employment Details
      Tab 3 — Education & Professional
      Tab 4 — Next of Kin & Guarantor
    """

    class Meta:
        model = Staff
        fields = [
            # ── Tab 1: Personal ──────────────────────────────
            "middle_name",
            "gender",
            "date_of_birth",
            "state_of_origin",
            "nationality",
            "marital_status",
            "phone_mobile",
            "phone_home",
            "personal_email",
            "official_email",
            "address",
            # ── Tab 2: Employment ────────────────────────────
            "employment_type",
            "employment_status",
            "staff_rank",
            "date_employed",
            "confirmation_date",
            "notes",
            # ── Tab 3: Education ────────────────────────────
            "qualification",
            "institution",
            "graduation_year",
            "professional_body",
            # ── Tab 4: Next of Kin & Guarantor ─────────────
            "next_of_kin_name",
            "next_of_kin_phone",
            "next_of_kin_address",
            "guarantor_name",
            "guarantor_phone",
            "guarantor_email",
            "guarantor_address",
        ]

        widgets = {
            # Tab 1 — Personal
            "middle_name":    _text("Optional"),
            "gender":         _select(),
            "date_of_birth":  _date(),
            "state_of_origin":_select(),
            "nationality":    _text("e.g. Nigerian"),
            "marital_status": _select(),
            "phone_mobile":   _text("+234 801 000 0000"),
            "phone_home":     _text("+234 1 000 0000"),
            "personal_email": _email("personal@email.com"),
            "official_email": _email("staff@company.com"),
            "address":        _textarea(2, "House number, street, city, state"),
            # Tab 2 — Employment
            "employment_type":   _select(),
            "employment_status": _select(),
            "staff_rank":        _select(),
            "date_employed":     _date(),
            "confirmation_date": _date(),
            "notes":             _textarea(3, "Internal notes about this staff member…"),
            # Tab 3 — Education
            "qualification":    _text("e.g. B.Sc Computer Science"),
            "institution":      _text("e.g. University of Lagos"),
            "graduation_year":  _number("e.g. 2018"),
            "professional_body":_text("e.g. ICAN, NIM, NSE"),
            # Tab 4 — Next of Kin & Guarantor
            "next_of_kin_name":    _text("Full name"),
            "next_of_kin_phone":   _text("+234 ..."),
            "next_of_kin_address": _textarea(2, "Address"),
            "guarantor_name":      _text("Full name"),
            "guarantor_phone":     _text("+234 ..."),
            "guarantor_email":     _email("guarantor@email.com"),
            "guarantor_address":   _textarea(2, "Address"),
        }

        labels = {
            "middle_name":       "Middle Name",
            "gender":            "Gender",
            "date_of_birth":     "Date of Birth",
            "state_of_origin":   "State of Origin",
            "nationality":       "Nationality",
            "marital_status":    "Marital Status",
            "phone_mobile":      "Mobile Phone",
            "phone_home":        "Home Phone",
            "personal_email":    "Personal Email",
            "official_email":    "Official Email",
            "address":           "Residential Address",
            "employment_type":   "Employment Type",
            "employment_status": "Employment Status",
            "staff_rank":        "Staff Rank / Grade",
            "date_employed":     "Date of Employment",
            "confirmation_date": "Confirmation Date",
            "notes":             "Internal Notes",
            "qualification":     "Highest Qualification",
            "institution":       "Institution / School",
            "graduation_year":   "Graduation Year",
            "professional_body": "Professional Body / Membership",
            "next_of_kin_name":    "Full Name",
            "next_of_kin_phone":   "Phone Number",
            "next_of_kin_address": "Address",
            "guarantor_name":      "Guarantor Full Name",
            "guarantor_phone":     "Guarantor Phone",
            "guarantor_email":     "Guarantor Email",
            "guarantor_address":   "Guarantor Address",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add blank prompt to all select fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.empty_label = "— Select —"

        # Required fields
        self.fields["date_of_birth"].required = True
        self.fields["date_employed"].required  = True
        self.fields["gender"].required         = True
        self.fields["state_of_origin"].required = True
        self.fields["phone_mobile"].required   = True
        self.fields["employment_type"].required = True
        self.fields["employment_status"].required = True

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get("date_of_birth")
        if dob:
            today = timezone.localdate()
            age = (
                today.year - dob.year
                - ((today.month, today.day) < (dob.month, dob.day))
            )
            if age < 16:
                raise ValidationError(
                    "Staff must be at least 16 years old."
                )
            if dob > today:
                raise ValidationError(
                    "Date of birth cannot be in the future."
                )
        return dob

    def clean_date_employed(self):
        date_employed = self.cleaned_data.get("date_employed")
        if date_employed and date_employed > timezone.localdate():
            raise ValidationError(
                "Employment date cannot be in the future."
            )
        return date_employed

    def clean_confirmation_date(self):
        confirmation_date = self.cleaned_data.get("confirmation_date")
        date_employed     = self.cleaned_data.get("date_employed")

        if confirmation_date and date_employed:
            if confirmation_date < date_employed:
                raise ValidationError(
                    "Confirmation date cannot be before the date of employment."
                )
        return confirmation_date

    def clean_graduation_year(self):
        year = self.cleaned_data.get("graduation_year")
        if year:
            current_year = timezone.localdate().year
            if year < 1950 or year > current_year:
                raise ValidationError(
                    f"Graduation year must be between 1950 and {current_year}."
                )
        return year

        
# Staff Attendance

class AttendanceDateForm(forms.Form):
    """
    Used for selecting attendance date.
    """

    date = forms.DateField(
        required=False,
        initial=timezone.localdate,
        widget=forms.DateInput(
            attrs={
                'type': 'date',
                'class': 'form-control'
            }
        )
    )


class StaffAttendanceForm(forms.ModelForm):

    teacher_name = forms.CharField(
        required=False,
        disabled=True,
        label='Teacher',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control'
            }
        )
    )

    class Meta:
        model = StaffAttendance

        fields = [
            'check_in_time',
            'check_out_time',
            'status',
            'remarks',
        ]

        widgets = {

            'check_in_time': forms.TimeInput(
                attrs={
                    'type': 'time',
                    'class': 'form-control'
                }
            ),

            'check_out_time': forms.TimeInput(
                attrs={
                    'type': 'time',
                    'class': 'form-control'
                }
            ),

            'status': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),

            'remarks': forms.Textarea(
                attrs={
                    'rows': 2,
                    'class': 'form-control'
                }
            ),
        }