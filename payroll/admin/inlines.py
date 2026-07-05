from django.contrib import admin

from payroll.models import (
    SalaryStructureItem,
    PayrollItem,
)


class SalaryStructureItemInline(admin.TabularInline):

    model = SalaryStructureItem

    extra = 1

    autocomplete_fields = [
        "component",
    ]


class PayrollItemInline(admin.TabularInline):

    model = PayrollItem

    extra = 0

    can_delete = False

    readonly_fields = (

        "component_name",

        "quantity",

        "rate",

        "amount",

    )