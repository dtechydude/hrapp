from django.contrib import admin

from .models import (
    AdvanceRepayment,
    BankSchedule,
    BankScheduleItem,
    Bonus,
    Payroll,
    PayrollApproval,
    PayrollItem,
    PayrollJournal,
    PayrollPayment,
    PayrollPaymentBatch,
    PayrollPeriod,
    PayrollRun,
    Payslip,
    Penalty,
    SalaryAdvance,
    SalaryAssignment,
    SalaryComponent,
    SalaryStructure,
    SalaryStructureItem,
    StaffAllowance,
    StaffBankAccount,
    StaffDeduction,
)


class SalaryStructureItemInline(admin.TabularInline):
    model = SalaryStructureItem
    extra = 1
    autocomplete_fields = ["component"]


@admin.register(SalaryComponent)
class SalaryComponentAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "category", "nature", "calculation_method", "is_active")
    list_filter = ("category", "nature", "calculation_method", "is_active", "is_statutory")
    search_fields = ("code", "name")
    ordering = ("category", "display_order")


@admin.register(SalaryStructure)
class SalaryStructureAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "company", "gross_salary", "net_salary", "is_active")
    list_filter = ("company", "is_active")
    search_fields = ("name", "code")
    inlines = [SalaryStructureItemInline]


@admin.register(SalaryAssignment)
class SalaryAssignmentAdmin(admin.ModelAdmin):
    list_display = ("staff", "salary_structure", "effective_from", "reason", "is_current")
    list_filter = ("is_current", "reason", "salary_structure")
    search_fields = ("staff__employee_no", "staff__user__first_name", "staff__user__last_name")
    autocomplete_fields = ["staff", "salary_structure"]


@admin.register(PayrollPeriod)
class PayrollPeriodAdmin(admin.ModelAdmin):
    list_display = ("company", "period_name", "status", "payroll_date", "is_locked")
    list_filter = ("status", "company", "year")
    search_fields = ("company__name",)
    readonly_fields = ("opened_at", "approved_at", "paid_at", "locked_at")


@admin.register(Payroll)
class PayrollAdmin(admin.ModelAdmin):
    list_display = (
        "staff", "payroll_period", "gross_salary", "total_deductions",
        "net_salary", "payment_status",
    )
    list_filter = ("payment_status", "payroll_period__company", "payroll_period")
    search_fields = ("staff__employee_no", "staff__user__first_name", "staff__user__last_name")
    autocomplete_fields = ["staff", "salary_assignment", "deployment"]
    readonly_fields = (
        "gross_salary", "total_earnings", "total_deductions",
        "taxable_income", "net_salary", "created_at", "updated_at",
    )


@admin.register(PayrollItem)
class PayrollItemAdmin(admin.ModelAdmin):
    list_display = ("payroll", "component_name", "nature", "quantity", "rate", "amount")
    list_filter = ("nature", "is_taxable", "is_pensionable", "is_statutory")
    search_fields = ("component_name", "component_code", "payroll__staff__employee_no")
    readonly_fields = ("amount", "component_name", "component_code", "component_order", "nature")


@admin.register(PayrollRun)
class PayrollRunAdmin(admin.ModelAdmin):
    list_display = ("payroll_period", "run_number", "total_staff", "successful", "failed", "is_completed")
    list_filter = ("is_completed", "payroll_period__company")


@admin.register(PayrollApproval)
class PayrollApprovalAdmin(admin.ModelAdmin):
    list_display = ("payroll", "level", "status", "assigned_to", "action_at")
    list_filter = ("level", "status")


@admin.register(PayrollJournal)
class PayrollJournalAdmin(admin.ModelAdmin):
    list_display = ("payroll", "account_name", "debit", "credit", "created_at")
    search_fields = ("account_name",)


@admin.register(Payslip)
class PayslipAdmin(admin.ModelAdmin):
    list_display = ("payslip_number", "employee", "payroll_period", "net_salary", "acknowledged")
    search_fields = ("payslip_number", "payroll__staff__employee_no")
    readonly_fields = ("payslip_number", "verification_token", "generated_at")


@admin.register(PayrollPaymentBatch)
class PayrollPaymentBatchAdmin(admin.ModelAdmin):
    list_display = ("batch_number", "batch_name", "payroll_period", "total_staff", "total_amount", "status")
    list_filter = ("status", "payroll_period__company")
    readonly_fields = ("batch_number", "total_staff", "total_amount")


@admin.register(PayrollPayment)
class PayrollPaymentAdmin(admin.ModelAdmin):
    list_display = ("payroll", "amount", "payment_method", "status", "payment_date")
    list_filter = ("status", "payment_method", "payment_channel")
    search_fields = ("payment_reference", "transaction_reference")


@admin.register(BankSchedule)
class BankScheduleAdmin(admin.ModelAdmin):
    list_display = ("schedule_number", "payroll_period", "total_staff", "total_amount", "exported")
    list_filter = ("exported", "payroll_period__company")
    readonly_fields = ("schedule_number", "total_staff", "total_amount")


@admin.register(BankScheduleItem)
class BankScheduleItemAdmin(admin.ModelAdmin):
    list_display = ("schedule", "staff", "bank_name", "account_number", "amount")
    search_fields = ("staff__employee_no", "account_number")


@admin.register(StaffBankAccount)
class StaffBankAccountAdmin(admin.ModelAdmin):
    list_display = ("staff", "bank_name", "account_number", "is_verified")
    search_fields = ("staff__employee_no", "account_number")
    autocomplete_fields = ["staff"]


@admin.register(StaffDeduction)
class StaffDeductionAdmin(admin.ModelAdmin):
    list_display = ("staff", "component", "frequency", "amount", "start_date", "is_suspended")
    list_filter = ("frequency", "is_suspended", "is_active")
    autocomplete_fields = ["staff", "component"]


@admin.register(StaffAllowance)
class StaffAllowanceAdmin(admin.ModelAdmin):
    list_display = ("staff", "component", "frequency", "amount", "start_date", "is_suspended")
    list_filter = ("frequency", "is_suspended", "is_active")
    autocomplete_fields = ["staff", "component"]


@admin.register(Bonus)
class BonusAdmin(admin.ModelAdmin):
    list_display = ("staff", "amount", "target_period", "status")
    list_filter = ("status", "target_period__company")
    autocomplete_fields = ["staff", "component"]


@admin.register(Penalty)
class PenaltyAdmin(admin.ModelAdmin):
    list_display = ("staff", "amount", "target_period", "status")
    list_filter = ("status", "target_period__company")
    autocomplete_fields = ["staff", "component"]


@admin.register(SalaryAdvance)
class SalaryAdvanceAdmin(admin.ModelAdmin):
    list_display = ("staff", "amount_requested", "amount_approved", "balance", "status")
    list_filter = ("status",)
    autocomplete_fields = ["staff", "component"]
    readonly_fields = ("balance",)


@admin.register(AdvanceRepayment)
class AdvanceRepaymentAdmin(admin.ModelAdmin):
    list_display = ("advance", "payroll", "amount", "created_at")
    readonly_fields = ("advance", "payroll", "amount", "created_at")

    def has_add_permission(self, request):
        # Repayments are only ever created by the payroll engine.
        return False

    def has_change_permission(self, request, obj=None):
        return False
