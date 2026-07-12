"""
leave/forms.py
───────────────────────────────────────────────────────────────────────────
LeaveRequestForm — the employee-facing application form.

Deliberately excludes `staff` and `status`: the staff member is inferred
from request.user in the view (never trusted from POST data), and status
always starts at Pending — set by the service layer, not the form.
───────────────────────────────────────────────────────────────────────────
"""
from django import forms

from .models import LeaveRequest, LeaveType


class LeaveRequestForm(forms.ModelForm):
    leave_type = forms.ModelChoiceField(
        queryset=LeaveType.objects.filter(is_active=True),
        empty_label="Select leave type...",
    )

    class Meta:
        model = LeaveRequest
        fields = ["leave_type", "start_date", "end_date", "reason"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "reason": forms.Textarea(attrs={"rows": 4, "placeholder": "Briefly explain the reason for this request..."}),
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_date")
        end = cleaned.get("end_date")
        if start and end and end < start:
            self.add_error("end_date", "End date cannot be before the start date.")
        return cleaned
