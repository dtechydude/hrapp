from django.contrib import admin

from payroll.models.payroll_payment import PayrollPayment


@admin.register(PayrollPayment)
class PayrollPaymentAdmin(admin.ModelAdmin):

    list_display = (
        "payment_reference",
        "payroll",
        # "amount_paid",
        "payment_method",
        "payment_date",
    )

    list_filter = (
        "payment_method",
        "payment_date",
    )

    search_fields = (
        "payment_reference",
    )

    readonly_fields = (
        "uuid",
        "created_at",
    )