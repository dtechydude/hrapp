from django.contrib import admin

from payroll.models.payroll_journal import PayrollJournal


@admin.register(PayrollJournal)
class PayrollJournalAdmin(admin.ModelAdmin):

    list_display = (
        # "journal_date",
        # "payroll_period",
        "description",
        # "total_debit",
        # "total_credit",
    )

    list_filter = (
        # "journal_date",
    )

    readonly_fields = (
        "uuid",
        "created_at",
    )