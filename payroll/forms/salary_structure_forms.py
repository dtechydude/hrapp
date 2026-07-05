from django import forms

from payroll.models import (
    SalaryStructure,
    SalaryStructureItem,
)


class SalaryStructureForm(forms.ModelForm):

    class Meta:

        model = SalaryStructure

        exclude = (
            "uuid",
            "created_at",
            "updated_at",
        )

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"


class SalaryStructureItemForm(forms.ModelForm):

    class Meta:

        model = SalaryStructureItem

        exclude = ()

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        for field in self.fields.values():

            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-check-input"

            else:
                field.widget.attrs["class"] = "form-control"


SalaryStructureItemFormSet = forms.inlineformset_factory(
    SalaryStructure,
    SalaryStructureItem,
    form=SalaryStructureItemForm,
    extra=1,
    can_delete=True,
)