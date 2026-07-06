from django.urls import path

from . import views

app_name = "payroll"

urlpatterns = [
    # Payroll periods — the core "run payroll" workflow
    path("periods/", views.PayrollPeriodListView.as_view(), name="period-list"),
    path("periods/new/", views.PayrollPeriodCreateView.as_view(), name="period-create"),
    path("periods/<int:pk>/", views.PayrollPeriodDetailView.as_view(), name="period-detail"),
    path("periods/<int:pk>/run/", views.RunPayrollView.as_view(), name="period-run"),
    path("periods/<int:pk>/approve/", views.ApprovePayrollPeriodView.as_view(), name="period-approve"),
    path("periods/<int:pk>/lock/", views.LockPayrollPeriodView.as_view(), name="period-lock"),
    path("periods/<int:pk>/export/", views.PayrollRegisterExportView.as_view(), name="period-export"),

    # Bank schedule
    path("periods/<int:pk>/bank-schedule/generate/", views.GenerateBankScheduleView.as_view(), name="bank-schedule-generate"),
    path("bank-schedule/<int:pk>/export/", views.BankScheduleExportView.as_view(), name="bank-schedule-export"),

    # Payslip
    path("payslip/<int:pk>/", views.PayslipPrintView.as_view(), name="payslip-print"),

    # Employee self-service — matches the URL names already referenced
    # (commented out, pending this) in employee_home.html
    path("my/payslips/", views.MyPayslipListView.as_view(), name="my_payslips"),
    path("my/payslips/<int:pk>/", views.MyPayslipPrintView.as_view(), name="my_payslip_print"),

    # Salary structures
    path("structures/", views.SalaryStructureListView.as_view(), name="structure-list"),
    path("structures/new/", views.SalaryStructureCreateView.as_view(), name="structure-create"),
    path("structures/<int:pk>/", views.SalaryStructureUpdateView.as_view(), name="structure-update"),

    # Variable pay inputs
    path("deductions/", views.StaffDeductionListView.as_view(), name="deduction-list"),
    path("deductions/new/", views.StaffDeductionCreateView.as_view(), name="deduction-create"),
    path("allowances/", views.StaffAllowanceListView.as_view(), name="allowance-list"),
    path("allowances/new/", views.StaffAllowanceCreateView.as_view(), name="allowance-create"),
    path("bonuses/new/", views.BonusCreateView.as_view(), name="bonus-create"),
    path("bonuses/<int:pk>/approve/", views.ApproveBonusView.as_view(), name="bonus-approve"),
    path("penalties/new/", views.PenaltyCreateView.as_view(), name="penalty-create"),
    path("penalties/<int:pk>/approve/", views.ApprovePenaltyView.as_view(), name="penalty-approve"),
    path("advances/", views.SalaryAdvanceListView.as_view(), name="advance-list"),
    path("advances/new/", views.SalaryAdvanceCreateView.as_view(), name="advance-create"),
    path("advances/<int:pk>/approve/", views.SalaryAdvanceApproveView.as_view(), name="advance-approve"),

    # Bank accounts
    path("bank-accounts/new/", views.StaffBankAccountCreateView.as_view(), name="bank-account-create"),
]
