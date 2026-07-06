from django import forms


class BootstrapModelForm(forms.ModelForm):
    """
    Applies Bootstrap 5 form-control / form-select classes to every
    field automatically. Any ModelForm in any app should subclass
    this instead of forms.ModelForm directly, so styling stays
    consistent without repeating widget attrs field by field.

    (This was originally defined inline in organization/forms.py —
    promoted here so payroll and every future app share the same
    implementation instead of redefining it per app.)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            is_select = isinstance(field.widget, (forms.Select, forms.SelectMultiple))
            css_class = "form-select" if is_select else "form-control"
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing} {css_class}".strip()
