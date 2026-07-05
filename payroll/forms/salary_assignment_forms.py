from django import forms

from payroll.models import SalaryAssignment


class SalaryAssignmentForm(forms.ModelForm):

    class Meta:

        model = SalaryAssignment

        exclude = (
            "uuid",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        )

        widgets = {

            "effective_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control",
                }
            )

        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        for field in self.fields.values():

            if "class" not in field.widget.attrs:

                if isinstance(field.widget, forms.CheckboxInput):
                    field.widget.attrs["class"] = "form-check-input"

                else:
                    field.widget.attrs["class"] = "form-control"