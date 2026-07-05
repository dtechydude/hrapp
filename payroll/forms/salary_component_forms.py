from django import forms

from payroll.models import SalaryComponent


class SalaryComponentForm(forms.ModelForm):

    class Meta:

        model = SalaryComponent

        exclude = (
            "uuid",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        )

        widgets = {

            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            )

        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        for field in self.fields.values():

            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-check-input"

            else:
                field.widget.attrs["class"] = "form-control"