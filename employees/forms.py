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



class StaffUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']

class StaffProfileForm(forms.ModelForm):
    class Meta:
        model = Staff
        exclude = ['user', 'created_by', 'updated_by', 'is_active', 'uuid', 'employee_no']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'date_employed': forms.DateInput(attrs={'type': 'date'}),
            'confirmation_date': forms.DateInput(attrs={'type': 'date'}),
        }
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