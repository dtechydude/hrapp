from django import forms

from payroll.models import PayrollPayment


class PayrollPaymentForm(forms.ModelForm):

    class Meta:

        model = PayrollPayment

        exclude = (
            "uuid",
            "created_at",
            "created_by",
        )

        widgets = {

            "payment_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control",
                }
            ),

            "remarks": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),

        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        for field in self.fields.values():

            if "class" not in field.widget.attrs:

                if isinstance(field.widget, forms.CheckboxInput):
                    field.widget.attrs["class"] = "form-check-input"

                else:
                    field.widget.attrs["class"] = "form-control"