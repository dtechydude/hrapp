from django import forms

from payroll.models import PayrollPeriod


class PayrollPeriodForm(forms.ModelForm):
    """
    Create/Edit Payroll Period
    """

    class Meta:
        model = PayrollPeriod

        fields = (
            "year",
            "month",
            "company",
            "remarks",
        )

        widgets = {
            "year": forms.NumberInput(
                attrs={"class": "form-control"}
            ),
            "month": forms.Select(
                attrs={"class": "form-select"}
            ),
            "company": forms.Select(
                attrs={"class": "form-select"}
            ),
            "remarks": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
        }

    def clean(self):

        cleaned = super().clean()

        year = cleaned.get("year")
        month = cleaned.get("month")
        company = cleaned.get("company")

        if PayrollPeriod.objects.filter(
            year=year,
            month=month,
            company=company,
        ).exists():

            raise forms.ValidationError(
                "Payroll Period already exists."
            )

        return cleaned