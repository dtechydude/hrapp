from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from core.exports import export_queryset_as_csv
from employees.mixins import StaffRequiredMixin

from .forms import (
    BonusForm,
    PayrollPeriodForm,
    PenaltyForm,
    SalaryAdvanceApprovalForm,
    SalaryAdvanceRequestForm,
    SalaryStructureForm,
    SalaryStructureItemFormSet,
    StaffAllowanceForm,
    StaffBankAccountForm,
    StaffDeductionForm,
)
from .models import (
    Bonus,
    BankSchedule,
    BankScheduleItem,
    Payroll,
    PayrollPeriod,
    Penalty,
    Payslip,
    SalaryAdvance,
    SalaryStructure,
    StaffAllowance,
    StaffDeduction,
)
from .services import run_payroll


# ─────────────────────────────────────────────────────────────
# Payroll Periods — the main "run payroll" workflow
# ─────────────────────────────────────────────────────────────

class PayrollPeriodListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = PayrollPeriod
    template_name = "payroll/payroll_period_list.html"
    context_object_name = "periods"
    paginate_by = 20
    permission_required = "payroll.view_payrollperiod"

    def get_queryset(self):
        return PayrollPeriod.objects.select_related("company").order_by("-year", "-month")


class PayrollPeriodCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = PayrollPeriod
    form_class = PayrollPeriodForm
    template_name = "payroll/payroll_period_form.html"
    permission_required = "payroll.add_payrollperiod"

    def form_valid(self, form):
        form.instance.generated_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f"Payroll period {self.object.period_name} created.")
        return response

    def get_success_url(self):
        return reverse("payroll:period-detail", args=[self.object.pk])


class PayrollPeriodDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """
    The main payroll-processing screen for one period: run payroll,
    review every staff member's gross/deductions/net, then approve,
    lock, or generate the bank schedule — all from one place.
    """

    model = PayrollPeriod
    template_name = "payroll/payroll_period_detail.html"
    context_object_name = "period"
    permission_required = "payroll.view_payrollperiod"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payrolls = (
            Payroll.objects.filter(payroll_period=self.object)
            .select_related("staff", "staff__user")
            .order_by("staff__user__last_name")
        )
        context["payrolls"] = payrolls
        context["total_gross"] = sum((p.gross_salary for p in payrolls), start=0)
        context["total_deductions"] = sum((p.total_deductions for p in payrolls), start=0)
        context["total_net"] = sum((p.net_salary for p in payrolls), start=0)
        context["runs"] = self.object.runs.all()[:5]
        return context


class RunPayrollView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """POST-only: triggers the payroll engine for one period."""

    permission_required = "payroll.add_payroll"

    def post(self, request, pk):
        period = get_object_or_404(PayrollPeriod, pk=pk)
        try:
            result = run_payroll(period, user=request.user)
        except ValidationError as exc:
            messages.error(request, str(exc))
        else:
            messages.success(
                request,
                f"Payroll run complete: {result.run.successful} succeeded, "
                f"{result.run.failed} failed out of {result.run.total_staff} staff.",
            )
            for failure in result.failures[:10]:
                messages.warning(request, f"{failure.staff.full_name}: {failure.error}")
        return redirect("payroll:period-detail", pk=period.pk)


class ApprovePayrollPeriodView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "payroll.change_payrollperiod"

    def post(self, request, pk):
        period = get_object_or_404(PayrollPeriod, pk=pk)
        period.approve(request.user)
        messages.success(request, f"{period.period_name} approved.")
        return redirect("payroll:period-detail", pk=period.pk)


class LockPayrollPeriodView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "payroll.change_payrollperiod"

    def post(self, request, pk):
        period = get_object_or_404(PayrollPeriod, pk=pk)
        period.lock(request.user)
        messages.success(request, f"{period.period_name} locked. It can no longer be modified.")
        return redirect("payroll:period-detail", pk=period.pk)


class PayrollRegisterExportView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Downloads every payroll in a period as CSV — the Payroll Register."""

    permission_required = "payroll.view_payroll"

    def get(self, request, pk):
        period = get_object_or_404(PayrollPeriod, pk=pk)
        queryset = (
            Payroll.objects.filter(payroll_period=period)
            .select_related("staff", "staff__user")
            .order_by("staff__user__last_name")
        )
        fields = [
            ("Employee No", lambda p: p.staff.employee_no),
            ("Staff Name", lambda p: p.staff.full_name),
            ("Gross Salary", "gross_salary"),
            ("Total Earnings", "total_earnings"),
            ("Total Deductions", "total_deductions"),
            ("Taxable Income", "taxable_income"),
            ("Net Salary", "net_salary"),
            ("Payment Status", "payment_status"),
        ]
        filename = f"payroll_register_{period.year}_{period.month:02d}.csv"
        return export_queryset_as_csv(queryset, fields, filename)


# ─────────────────────────────────────────────────────────────
# Bank Schedule
# ─────────────────────────────────────────────────────────────

class GenerateBankScheduleView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    Builds a BankSchedule + one BankScheduleItem per staff member
    with a completed payroll for this period, snapshotting bank
    details at generation time (never live-linked — see
    StaffBankAccount's docstring).
    """

    permission_required = "payroll.add_payroll"

    def post(self, request, pk):
        period = get_object_or_404(PayrollPeriod, pk=pk)
        payrolls = Payroll.objects.filter(payroll_period=period).select_related("staff")

        schedule = BankSchedule.objects.create(payroll_period=period, generated_by=request.user)

        skipped = []
        for payroll in payrolls:
            bank_account = getattr(payroll.staff, "bank_account", None)
            if not bank_account:
                skipped.append(payroll.staff.full_name)
                continue
            BankScheduleItem.objects.create(
                schedule=schedule,
                staff=payroll.staff,
                account_name=bank_account.account_name,
                account_number=bank_account.account_number,
                bank_name=bank_account.bank_name,
                amount=payroll.net_salary,
                narration=f"Salary - {period.period_name}",
            )

        if skipped:
            messages.warning(
                request,
                f"Bank schedule generated, but {len(skipped)} staff have no bank "
                f"account on file and were skipped: {', '.join(skipped[:10])}",
            )
        else:
            messages.success(request, f"Bank schedule {schedule.schedule_number} generated.")
        return redirect("payroll:period-detail", pk=period.pk)


class BankScheduleExportView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "payroll.view_payroll"

    def get(self, request, pk):
        schedule = get_object_or_404(BankSchedule, pk=pk)
        queryset = schedule.items.select_related("staff").order_by("staff__user__last_name")
        fields = [
            ("Employee No", lambda i: i.staff.employee_no),
            ("Account Name", "account_name"),
            ("Account Number", "account_number"),
            ("Bank Name", "bank_name"),
            ("Amount", "amount"),
            ("Narration", "narration"),
        ]
        return export_queryset_as_csv(queryset, fields, f"{schedule.schedule_number}.csv")


# ─────────────────────────────────────────────────────────────
# Payslip
# ─────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────
# Payslip
# ─────────────────────────────────────────────────────────────

class PayslipRenderMixin:
    """
    Shared rendering logic for any "show me this payslip" view.
    Subclasses only need to define get_queryset() — the difference
    between the admin view and the employee self-service view is
    entirely about WHICH payrolls they're allowed to see, not how
    the payslip itself is built or recorded.
    """

    model = Payroll
    template_name = "payroll/payslip_print.html"
    context_object_name = "payroll"

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        payslip, _ = Payslip.objects.get_or_create(
            payroll=self.object, defaults={"generated_by": request.user}
        )
        payslip.record_print()
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["earnings"] = self.object.items.filter(nature="Earning")
        context["deductions"] = self.object.items.filter(nature="Deduction")
        context["generated_at"] = timezone.now()
        return context


class PayslipPrintView(LoginRequiredMixin, PermissionRequiredMixin, PayslipRenderMixin, DetailView):
    """
    Admin/payroll-officer view of any staff member's payslip — same
    zero-dependency print-to-PDF approach as the organization report.
    """

    permission_required = "payroll.view_payroll"

    def get_queryset(self):
        return Payroll.objects.select_related(
            "staff", "staff__user", "payroll_period", "payroll_period__company"
        ).prefetch_related("items")


class MyPayslipListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    """
    Employee self-service: "My Payslips" — the full history behind
    the "Recent Payslips" widget on the employee dashboard. No
    special permission required beyond being logged in; a staff
    member only ever sees their OWN payroll records, enforced by the
    queryset itself rather than a Django permission (an ordinary
    staff member should never need payroll.view_payroll just to see
    their own pay). StaffRequiredMixin supplies self.staff and raises
    the same friendly PermissionDenied used by DashboardHomeView if
    the account has no linked staff profile.
    """

    model = Payroll
    template_name = "payroll/my_payslips.html"
    context_object_name = "payrolls"
    paginate_by = 12

    def get_queryset(self):
        return (
            Payroll.objects.filter(staff=self.staff)
            .select_related("payroll_period", "payroll_period__company")
            .order_by("-payroll_period__year", "-payroll_period__month")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["staff"] = self.staff
        return context


class MyPayslipPrintView(LoginRequiredMixin, StaffRequiredMixin, PayslipRenderMixin, DetailView):
    """
    Employee self-service payslip view/print. Filtering the queryset
    to `staff=self.staff` means requesting someone else's payroll ID
    404s (record not found in "your" queryset) rather than 403ing —
    this avoids confirming to a curious staff member that a given
    payroll ID belongs to a real colleague.
    """

    def get_queryset(self):
        return Payroll.objects.filter(staff=self.staff).select_related(
            "staff", "staff__user", "payroll_period", "payroll_period__company"
        ).prefetch_related("items")


# ─────────────────────────────────────────────────────────────
# Salary Structures
# ─────────────────────────────────────────────────────────────

class SalaryStructureListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = SalaryStructure
    template_name = "payroll/salary_structure_list.html"
    context_object_name = "structures"
    permission_required = "payroll.view_salarystructure"

    def get_queryset(self):
        return SalaryStructure.objects.select_related("company").order_by("company__name", "name")


class SalaryStructureCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = SalaryStructure
    form_class = SalaryStructureForm
    template_name = "payroll/salary_structure_form.html"
    permission_required = "payroll.add_salarystructure"

    def get_success_url(self):
        return reverse("payroll:structure-update", args=[self.object.pk])


class SalaryStructureUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Edits a structure and its line items on one page via an inline formset."""

    model = SalaryStructure
    form_class = SalaryStructureForm
    template_name = "payroll/salary_structure_form.html"
    permission_required = "payroll.change_salarystructure"

    def get_success_url(self):
        return reverse("payroll:structure-update", args=[self.object.pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["formset"] = SalaryStructureItemFormSet(
            self.request.POST or None, instance=self.object
        )
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context["formset"]
        if formset.is_valid():
            response = super().form_valid(form)
            formset.instance = self.object
            formset.save()
            messages.success(self.request, "Salary structure updated.")
            return response
        return self.render_to_response(self.get_context_data(form=form))


# ─────────────────────────────────────────────────────────────
# Variable pay inputs — deductions, allowances, bonuses, penalties, advances
# ─────────────────────────────────────────────────────────────

class StaffDeductionListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = StaffDeduction
    template_name = "payroll/staff_deduction_list.html"
    context_object_name = "deductions"
    permission_required = "payroll.view_staffdeduction"

    def get_queryset(self):
        return StaffDeduction.objects.filter(is_active=True).select_related("staff", "component")


class StaffDeductionCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = StaffDeduction
    form_class = StaffDeductionForm
    template_name = "payroll/staff_deduction_form.html"
    success_url = reverse_lazy("payroll:deduction-list")
    permission_required = "payroll.add_staffdeduction"


class StaffAllowanceListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = StaffAllowance
    template_name = "payroll/staff_allowance_list.html"
    context_object_name = "allowances"
    permission_required = "payroll.view_staffallowance"

    def get_queryset(self):
        return StaffAllowance.objects.filter(is_active=True).select_related("staff", "component")


class StaffAllowanceCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = StaffAllowance
    form_class = StaffAllowanceForm
    template_name = "payroll/staff_allowance_form.html"
    success_url = reverse_lazy("payroll:allowance-list")
    permission_required = "payroll.add_staffallowance"


class BonusCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Bonus
    form_class = BonusForm
    template_name = "payroll/bonus_form.html"
    success_url = reverse_lazy("payroll:period-list")
    permission_required = "payroll.add_bonus"

    def form_valid(self, form):
        form.instance.requested_by = self.request.user
        return super().form_valid(form)


class ApproveBonusView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "payroll.change_bonus"

    def post(self, request, pk):
        bonus = get_object_or_404(Bonus, pk=pk)
        bonus.approve(request.user)
        messages.success(request, f"Bonus for {bonus.staff.full_name} approved.")
        return redirect("payroll:period-detail", pk=bonus.target_period_id)


class PenaltyCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Penalty
    form_class = PenaltyForm
    template_name = "payroll/penalty_form.html"
    success_url = reverse_lazy("payroll:period-list")
    permission_required = "payroll.add_penalty"

    def form_valid(self, form):
        form.instance.imposed_by = self.request.user
        return super().form_valid(form)


class ApprovePenaltyView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "payroll.change_penalty"

    def post(self, request, pk):
        penalty = get_object_or_404(Penalty, pk=pk)
        penalty.approve(request.user)
        messages.success(request, f"Penalty for {penalty.staff.full_name} approved.")
        return redirect("payroll:period-detail", pk=penalty.target_period_id)


class SalaryAdvanceListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = SalaryAdvance
    template_name = "payroll/salary_advance_list.html"
    context_object_name = "advances"
    permission_required = "payroll.view_salaryadvance"

    def get_queryset(self):
        return SalaryAdvance.objects.select_related("staff").order_by("-requested_at")


class SalaryAdvanceCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = SalaryAdvance
    form_class = SalaryAdvanceRequestForm
    template_name = "payroll/salary_advance_form.html"
    success_url = reverse_lazy("payroll:advance-list")
    permission_required = "payroll.add_salaryadvance"


class SalaryAdvanceApproveView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = SalaryAdvance
    form_class = SalaryAdvanceApprovalForm
    template_name = "payroll/salary_advance_approve.html"
    success_url = reverse_lazy("payroll:advance-list")
    permission_required = "payroll.change_salaryadvance"

    def form_valid(self, form):
        advance = form.save(commit=False)
        advance.approve(
            self.request.user,
            amount_approved=form.cleaned_data["amount_approved"],
            monthly_deduction=form.cleaned_data["monthly_deduction"],
            comments=form.cleaned_data["comments"],
        )
        messages.success(self.request, f"Advance for {advance.staff.full_name} approved.")
        return redirect(self.success_url)


class StaffBankAccountCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    form_class = StaffBankAccountForm
    template_name = "payroll/staff_bank_account_form.html"
    success_url = reverse_lazy("payroll:period-list")
    permission_required = "payroll.add_staffbankaccount"


import csv
from datetime import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import HttpResponse
from django.views.generic import ListView, View

from .models import StaffBankAccount


class ManagerRequiredMixin(LoginRequiredMixin):
    """Superusers or is_staff only. Swap for an existing equivalent
    mixin in your project if you already have one (e.g.
    employees.mixins.StaffManagerRequiredMixin) — behavior is identical."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied("You do not have permission to view staff bank details.")
        return super().dispatch(request, *args, **kwargs)


class StaffBankAccountListView(ManagerRequiredMixin, ListView):
    """
    URL: /payroll/bank-accounts/   (name: payroll:bank-account-list)

    Query params:
      ?q=search        matches staff name, employee no, bank name, or account number
      ?bank=Bank+Name   exact-match filter, populated from the distinct bank list
    """

    model = StaffBankAccount
    template_name = "payroll/staff_bankaccount_list.html"
    context_object_name = "accounts"
    paginate_by = 25

    def get_queryset(self):
        qs = (
            StaffBankAccount.objects.filter(is_active=True)
            .select_related("staff", "staff__user")
            .order_by("staff__user__first_name", "staff__user__last_name")
        )

        query = self.request.GET.get("q", "").strip()
        if query:
            qs = qs.filter(
                Q(staff__user__first_name__icontains=query)
                | Q(staff__user__last_name__icontains=query)
                | Q(staff__employee_no__icontains=query)
                | Q(bank_name__icontains=query)
                | Q(account_number__icontains=query)
            )

        bank = self.request.GET.get("bank", "").strip()
        if bank:
            qs = qs.filter(bank_name=bank)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Staff Bank Accounts"
        ctx["breadcrumb"] = "Staff Bank Accounts"
        ctx["query"] = self.request.GET.get("q", "")
        ctx["current_bank"] = self.request.GET.get("bank", "")
        ctx["bank_choices"] = (
            StaffBankAccount.objects.filter(is_active=True)
            .order_by("bank_name")
            .values_list("bank_name", flat=True)
            .distinct()
        )
        ctx["total_count"] = self.get_queryset().count()
        ctx["missing_count"] = (
            self.model.objects.filter(is_active=True).exclude(
                account_number__isnull=False
            ).count()
            if hasattr(self.model, "account_number")
            else 0
        )
        return ctx


class StaffBankAccountExportCSVView(ManagerRequiredMixin, View):
    """
    URL: /payroll/bank-accounts/export/   (name: payroll:bank-account-export)

    Exports whatever the current search/filter would show in the list
    view (same ?q= and ?bank= params honored) — so "export what I'm
    looking at" just works, rather than always exporting everything.
    """

    def get(self, request, *args, **kwargs):
        qs = (
            StaffBankAccount.objects.filter(is_active=True)
            .select_related("staff", "staff__user")
            .order_by("staff__user__first_name", "staff__user__last_name")
        )

        query = request.GET.get("q", "").strip()
        if query:
            qs = qs.filter(
                Q(staff__user__first_name__icontains=query)
                | Q(staff__user__last_name__icontains=query)
                | Q(staff__employee_no__icontains=query)
                | Q(bank_name__icontains=query)
                | Q(account_number__icontains=query)
            )

        bank = request.GET.get("bank", "").strip()
        if bank:
            qs = qs.filter(bank_name=bank)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="staff_bank_accounts_{timestamp}.csv"'

        writer = csv.writer(response)
        writer.writerow([
            "Employee No", "Full Name", "Bank Name",
            "Account Number", "Account Name", "Department", "Status",
        ])

        for acc in qs:
            deployment = getattr(acc.staff, "current_deployment", None)
            writer.writerow([
                acc.staff.employee_no,
                acc.staff.full_name,
                acc.bank_name,
                acc.account_number,
                acc.account_name,
                getattr(deployment, "department", "") if deployment else "",
                acc.staff.employment_status,
            ])

        return response