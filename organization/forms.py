from django import forms
from django.utils import timezone

from employees.models import Staff

from .models import Company, Department, StaffDeployment, StaffRole


class BootstrapModelForm(forms.ModelForm):
    """
    Applies Bootstrap 5 form-control / form-select classes to every
    field automatically, so individual forms across the project don't
    need to repeat widget attrs field by field. Any project ModelForm
    can subclass this instead of forms.ModelForm directly.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            is_select = isinstance(field.widget, (forms.Select, forms.SelectMultiple))
            css_class = "form-select" if is_select else "form-control"
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing} {css_class}".strip()


class StaffDeploymentForm(BootstrapModelForm):
    """
    Form used to deploy or redeploy a staff member. Saving is handled
    entirely by organization.services.deploy_staff() — this form only
    validates and hands back clean data; it never calls form.save()
    directly, because "saving" here means running the close-previous /
    open-new transaction, not a plain model save.
    """

    start_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        initial=timezone.localdate,
        help_text="Date the staff member resumes at the new posting.",
    )

    class Meta:
        model = StaffDeployment
        fields = ["staff", "company", "department", "designation", "start_date"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["staff"].queryset = (
            Staff.objects.filter(is_active=True)
            .select_related("user")
            .order_by("user__last_name", "user__first_name")
        )
        self.fields["company"].queryset = Company.objects.order_by("name")
        self.fields["department"].queryset = Department.objects.order_by("name")
        self.fields["designation"].queryset = StaffRole.objects.order_by("name")
        self.fields["staff"].label = "Staff Member"
        self.fields["designation"].label = "Designation / Role at Client"
