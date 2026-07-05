from django.contrib import admin

from payroll.models.payroll_period import PayrollPeriod


@admin.register(PayrollPeriod)
class PayrollPeriodAdmin(admin.ModelAdmin):

    list_display = (
        "period_name",
        "year",
        "month",
        "status",
        # "total_staff",
        # "total_amount",
        "created_at",
    )

    list_filter = (
        "status",
        "year",
        "month",
    )

    search_fields = (
        "period_name",
    )

    readonly_fields = (
        "uuid",
        "created_at",
        "updated_at",
        # "total_staff",
        # "total_amount",
    )

    ordering = (
        "-year",
        "-month",
    )