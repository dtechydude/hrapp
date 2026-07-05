from django.contrib import admin

from payroll.models.payroll import Payroll
from payroll.models.payroll_item import PayrollItem


class PayrollItemInline(admin.TabularInline):

    model = PayrollItem

    extra = 0

    readonly_fields = (
        "component_name",
        "amount",
    )


@admin.register(Payroll)
class PayrollAdmin(admin.ModelAdmin):

    list_display = (
        "staff",
        "payroll_period",
        "gross_salary",
        "net_salary",
        "payment_status",
    )

    list_filter = (
        "payment_status",
        "payroll_period",
    )

    search_fields = (
        "staff__employee_no",
        "staff__user__first_name",
        "staff__user__last_name",
    )

    autocomplete_fields = (
        "staff",
        "payroll_period",
    )

    # readonly_fields = (
    #     "uuid",
    #     "gross_salary",
    #     "net_salary",
    #     "total_allowances",
    #     "total_deductions",
    #     "created_at",
    #     "updated_at",
    # )

    inlines = [
        PayrollItemInline,
    ]