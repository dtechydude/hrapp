from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone

from core.forms import BootstrapModelForm
from employees.models import Staff
from organization.models import Company

from .models import (
    Bonus,
    Penalty,
    PayrollPeriod,
    SalaryAdvance,
    SalaryComponent,
    SalaryStructure,
    SalaryStructureItem,
    StaffAllowance,
    StaffBankAccount,
    StaffDeduction,
)

from payroll. models import ComponentNature
from .models import SalaryAdvance, SalaryComponent


class PayrollPeriodForm(BootstrapModelForm):
    class Meta:
        model = PayrollPeriod
        fields = ["company", "month", "year", "payroll_date", "remarks"]
        widgets = {"payroll_date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["company"].queryset = Company.objects.filter(is_active=True).order_by("name")
        self.fields["year"].initial = timezone.localdate().year


class SalaryComponentForm(BootstrapModelForm):
    class Meta:
        model = SalaryComponent
        fields = [
            "code", "name", "category", "nature", "calculation_method",
            "default_amount", "percentage", "percentage_of", "apply_on_gross",
            "is_taxable", "is_pensionable", "is_statutory",
            "affects_gross", "affects_net", "formula", "display_order",
            "is_editable", "is_proratable", "show_on_payslip", "description",
        ]


class SalaryStructureForm(BootstrapModelForm):
    class Meta:
        model = SalaryStructure
        fields = ["company", "name", "code", "description", "effective_from", "effective_to"]
        widgets = {
            "effective_from": forms.DateInput(attrs={"type": "date"}),
            "effective_to": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["company"].queryset = Company.objects.filter(is_active=True).order_by("name")


class SalaryStructureItemForm(BootstrapModelForm):
    class Meta:
        model = SalaryStructureItem
        fields = ["component", "amount", "percentage", "formula_override", "display_order"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["component"].queryset = SalaryComponent.objects.filter(is_active=True).order_by(
            "category", "display_order"
        )


# Manage a salary structure's line items inline on the same page as
# the structure itself — this is the "define once, reuse for every
# staff on this structure" screen.
SalaryStructureItemFormSet = inlineformset_factory(
    SalaryStructure,
    SalaryStructureItem,
    form=SalaryStructureItemForm,
    extra=1,
    can_delete=True,
)


class _StaffScopedForm(BootstrapModelForm):
    """Shared setup for the four variable-pay-input forms below —
    scopes the staff dropdown to active staff and sorts it usefully."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "staff" in self.fields:
            self.fields["staff"].queryset = (
                Staff.objects.filter(is_active=True)
                .select_related("user")
                .order_by("user__last_name", "user__first_name")
            )
        if "component" in self.fields:
            self.fields["component"].queryset = SalaryComponent.objects.filter(is_active=True)


class StaffDeductionForm(_StaffScopedForm):
    class Meta:
        model = StaffDeduction
        fields = ["staff", "component", "frequency", "amount", "start_date", "end_date", "reason"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }


class StaffAllowanceForm(_StaffScopedForm):
    class Meta:
        model = StaffAllowance
        fields = ["staff", "component", "frequency", "amount", "start_date", "end_date", "reason"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }


class BonusForm(_StaffScopedForm):
    class Meta:
        model = Bonus
        fields = ["staff", "component", "amount", "target_period", "reason"]


class PenaltyForm(_StaffScopedForm):
    class Meta:
        model = Penalty
        fields = ["staff", "component", "amount", "target_period", "reason"]


class SalaryAdvanceRequestForm(_StaffScopedForm):
    """What HR/the staff member fills in when requesting an advance —
    approval amount/installment are set separately by whoever approves it."""

    class Meta:
        model = SalaryAdvance
        fields = ["staff", "component", "amount_requested", "reason"]


class SalaryAdvanceApprovalForm(BootstrapModelForm):
    """What the approver fills in — deliberately separate from the
    request form so a staff member can never set their own approved
    amount or monthly deduction."""

    class Meta:
        model = SalaryAdvance
        fields = ["amount_approved", "monthly_deduction", "comments"]


class StaffBankAccountForm(_StaffScopedForm):
    class Meta:
        model = StaffBankAccount
        fields = ["staff", "bank_name", "bank_code", "account_name", "account_number", "bvn"]


# ─────────────────────────────────────────────────────────────
# Append to payroll/forms.py — new form, does not touch
# SalaryAdvanceRequestForm or SalaryAdvanceApprovalForm.
# ─────────────────────────────────────────────────────────────

class MySalaryAdvanceRequestForm(forms.ModelForm):
    """
    Employee self-service version of the advance request.

    Deliberately excludes `staff`, `status`, `amount_approved`,
    `monthly_deduction`, and `balance` — staff is set from the logged-in
    user in the view (never trusted from POST data), status defaults to
    PENDING on the model itself, and the rest are HR/approval-time
    fields the employee has no business setting.

    `component` is still asked for here because SalaryAdvance.component
    is a required FK with no default — the employee picks which
    deduction-nature payroll component this advance repays through,
    limited to the same Deduction-nature constraint the model's own
    clean() already enforces.
    """

    component = forms.ModelChoiceField(
        queryset=SalaryComponent.objects.filter(
            nature=ComponentNature.DEDUCTION, is_active=True
        ),
        label="Repayment Deduction Line",
        help_text="Which payroll deduction this advance will be repaid through.",
        empty_label="Select...",
    )

    class Meta:
        model = SalaryAdvance
        fields = ["component", "amount_requested", "reason"]
        widgets = {
            "reason": forms.Textarea(
                attrs={"rows": 3, "placeholder": "Briefly explain why you need this advance..."}
            ),
        }

    def clean_amount_requested(self):
        amount = self.cleaned_data["amount_requested"]
        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount

