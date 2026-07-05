from django.contrib import admin

from payroll.models.payslip import Payslip


@admin.register(Payslip)
class PayslipAdmin(admin.ModelAdmin):

    list_display = (
        "payslip_number",
        "employee",
        "payroll_period",
        "net_salary",
        "generated_at",
    )

    list_filter = (
        "generated_at",
    )

    search_fields = (
        "payslip_number",
        "payroll__staff__employee_no",
    )

    readonly_fields = (
        "uuid",
        "verification_token",
        "download_count",
        "print_count",
        "generated_at",
    )