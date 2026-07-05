# from django.contrib import messages
# from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
# from django.core.exceptions import ValidationError
# from django.shortcuts import get_object_or_404, redirect
# from django.urls import reverse_lazy
# from django.utils import timezone
# from django.views import View
# from django.views.generic import CreateView, ListView

# from employees.models import Staff

# from .forms import StaffDeploymentForm
# from .models import Company, Department, StaffDeployment
# from .services import deploy_staff, end_deployment


# class DeploymentListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
#     """
#     Admin-facing view of every staff member's current posting and
#     location. This is the primary "where is everyone right now"
#     screen for HR, branch managers and auditors.

#     Filtering/search happen server-side via GET params so the result
#     is bookmarkable/shareable and works with JavaScript disabled.
#     """

#     model = StaffDeployment
#     template_name = "organization/deployment_list.html"
#     context_object_name = "deployments"
#     paginate_by = 25
#     permission_required = "organization.view_staffdeployment"

#     def get_queryset(self):
#         qs = StaffDeployment.objects.current()

#         company_id = self.request.GET.get("company")
#         department_id = self.request.GET.get("department")
#         search_term = self.request.GET.get("q", "")

#         if company_id:
#             qs = qs.for_company(company_id)
#         if department_id:
#             qs = qs.for_department(department_id)
#         if search_term:
#             qs = qs.search(search_term)

#         return qs.order_by("company__name", "staff__user__last_name")

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)

#         current_qs = StaffDeployment.objects.current()
#         deployed_staff_ids = current_qs.values_list("staff_id", flat=True)

#         context["companies"] = Company.objects.order_by("name")
#         context["departments"] = Department.objects.order_by("name")
#         context["selected_company"] = self.request.GET.get("company", "")
#         context["selected_department"] = self.request.GET.get("department", "")
#         context["search_term"] = self.request.GET.get("q", "")

#         context["stats"] = {
#             "total_deployed": current_qs.count(),
#             "total_companies": current_qs.values("company").distinct().count(),
#             "total_departments": current_qs.values("department").distinct().count(),
#             "unassigned_staff": Staff.objects.filter(is_active=True)
#             .exclude(id__in=deployed_staff_ids)
#             .count(),
#         }
#         return context


# class DeploymentCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
#     """
#     Deploys or redeploys a staff member. Deliberately does NOT call
#     ModelForm.save() — the actual write goes through
#     organization.services.deploy_staff() so the close-previous /
#     open-new transaction and validation rules are always applied,
#     regardless of how many places in the codebase end up calling this.
#     """

#     form_class = StaffDeploymentForm
#     template_name = "organization/deployment_form.html"
#     permission_required = "organization.add_staffdeployment"
#     success_url = reverse_lazy("organization:deployment-list")

#     def form_valid(self, form):
#         try:
#             result = deploy_staff(
#                 staff=form.cleaned_data["staff"],
#                 company=form.cleaned_data["company"],
#                 department=form.cleaned_data["department"],
#                 designation=form.cleaned_data["designation"],
#                 start_date=form.cleaned_data["start_date"],
#                 performed_by=self.request.user,
#             )
#         except ValidationError as exc:
#             form.add_error(None, exc)
#             return self.form_invalid(form)

#         if result.previous_deployment:
#             messages.success(
#                 self.request,
#                 f"{result.deployment.staff.full_name} redeployed to "
#                 f"{result.deployment.company.name}. Previous posting closed "
#                 f"and kept in history.",
#             )
#         else:
#             messages.success(
#                 self.request,
#                 f"{result.deployment.staff.full_name} deployed to "
#                 f"{result.deployment.company.name}.",
#             )
#         return redirect(self.success_url)

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context["is_create"] = True
#         return context


# class DeploymentHistoryView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
#     """
#     Full, immutable posting history for a single staff member —
#     every past and present deployment, oldest actions never edited
#     or removed.
#     """

#     model = StaffDeployment
#     template_name = "organization/deployment_history.html"
#     context_object_name = "deployments"
#     permission_required = "organization.view_staffdeployment"

#     def get_queryset(self):
#         self.staff = get_object_or_404(Staff, pk=self.kwargs["staff_id"])
#         return StaffDeployment.objects.filter(staff=self.staff).order_by("-start_date")

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context["staff"] = self.staff
#         return context


# class EndDeploymentView(LoginRequiredMixin, PermissionRequiredMixin, View):
#     """
#     Closes a current deployment without opening a new one (e.g. staff
#     pulled off a client site, awaiting a new posting). POST-only.
#     """

#     permission_required = "organization.change_staffdeployment"

#     def post(self, request, pk):
#         deployment = get_object_or_404(StaffDeployment, pk=pk, is_current=True)
#         try:
#             end_deployment(
#                 deployment=deployment,
#                 end_date=timezone.localdate(),
#                 performed_by=request.user,
#             )
#         except ValidationError as exc:
#             messages.error(request, str(exc))
#         else:
#             messages.success(
#                 request,
#                 f"Deployment of {deployment.staff.full_name} at "
#                 f"{deployment.company.name} has been ended.",
#             )
#         return redirect("organization:deployment-list")


# from django.contrib import messages
# from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
# from django.core.exceptions import ValidationError
# from django.shortcuts import get_object_or_404, redirect
# from django.urls import reverse_lazy
# from django.utils import timezone
# from django.views import View
# from django.views.generic import CreateView, ListView

# from employees.models import Staff

# from core.exports import export_queryset_as_csv

# from .forms import StaffDeploymentForm
# from .models import Company, Department, StaffDeployment
# from .services import deploy_staff, end_deployment


# class DeploymentListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
#     """
#     Admin-facing view of every staff member's current posting and
#     location. This is the primary "where is everyone right now"
#     screen for HR, branch managers and auditors.

#     Filtering/search happen server-side via GET params so the result
#     is bookmarkable/shareable and works with JavaScript disabled.
#     """

#     model = StaffDeployment
#     template_name = "organization/deployment_list.html"
#     context_object_name = "deployments"
#     paginate_by = 25
#     permission_required = "organization.view_staffdeployment"

#     def get_queryset(self):
#         qs = StaffDeployment.objects.current()

#         company_id = self.request.GET.get("company")
#         department_id = self.request.GET.get("department")
#         search_term = self.request.GET.get("q", "")

#         if company_id:
#             qs = qs.for_company(company_id)
#         if department_id:
#             qs = qs.for_department(department_id)
#         if search_term:
#             qs = qs.search(search_term)

#         return qs.order_by("company__name", "staff__user__last_name")

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)

#         current_qs = StaffDeployment.objects.current()
#         deployed_staff_ids = current_qs.values_list("staff_id", flat=True)

#         context["companies"] = Company.objects.order_by("name")
#         context["departments"] = Department.objects.order_by("name")
#         context["selected_company"] = self.request.GET.get("company", "")
#         context["selected_department"] = self.request.GET.get("department", "")
#         context["search_term"] = self.request.GET.get("q", "")

#         context["stats"] = {
#             "total_deployed": current_qs.count(),
#             "total_companies": current_qs.values("company").distinct().count(),
#             "total_departments": current_qs.values("department").distinct().count(),
#             "unassigned_staff": Staff.objects.filter(is_active=True)
#             .exclude(id__in=deployed_staff_ids)
#             .count(),
#         }
#         return context


# class DeploymentCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
#     """
#     Deploys or redeploys a staff member. Deliberately does NOT call
#     ModelForm.save() — the actual write goes through
#     organization.services.deploy_staff() so the close-previous /
#     open-new transaction and validation rules are always applied,
#     regardless of how many places in the codebase end up calling this.
#     """

#     form_class = StaffDeploymentForm
#     template_name = "organization/deployment_form.html"
#     permission_required = "organization.add_staffdeployment"
#     success_url = reverse_lazy("organization:deployment-list")

#     def form_valid(self, form):
#         try:
#             result = deploy_staff(
#                 staff=form.cleaned_data["staff"],
#                 company=form.cleaned_data["company"],
#                 department=form.cleaned_data["department"],
#                 designation=form.cleaned_data["designation"],
#                 start_date=form.cleaned_data["start_date"],
#                 performed_by=self.request.user,
#             )
#         except ValidationError as exc:
#             form.add_error(None, exc)
#             return self.form_invalid(form)

#         if result.previous_deployment:
#             messages.success(
#                 self.request,
#                 f"{result.deployment.staff.full_name} redeployed to "
#                 f"{result.deployment.company.name}. Previous posting closed "
#                 f"and kept in history.",
#             )
#         else:
#             messages.success(
#                 self.request,
#                 f"{result.deployment.staff.full_name} deployed to "
#                 f"{result.deployment.company.name}.",
#             )
#         return redirect(self.success_url)

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context["is_create"] = True
#         return context


# class DeploymentHistoryView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
#     """
#     Full, immutable posting history for a single staff member —
#     every past and present deployment, oldest actions never edited
#     or removed.
#     """

#     model = StaffDeployment
#     template_name = "organization/deployment_history.html"
#     context_object_name = "deployments"
#     permission_required = "organization.view_staffdeployment"

#     def get_queryset(self):
#         self.staff = get_object_or_404(Staff, pk=self.kwargs["staff_id"])
#         return StaffDeployment.objects.filter(staff=self.staff).order_by("-start_date")

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context["staff"] = self.staff
#         return context


# class EndDeploymentView(LoginRequiredMixin, PermissionRequiredMixin, View):
#     """
#     Closes a current deployment without opening a new one (e.g. staff
#     pulled off a client site, awaiting a new posting). POST-only.
#     """

#     permission_required = "organization.change_staffdeployment"

#     def post(self, request, pk):
#         deployment = get_object_or_404(StaffDeployment, pk=pk, is_current=True)
#         try:
#             end_deployment(
#                 deployment=deployment,
#                 end_date=timezone.localdate(),
#                 performed_by=request.user,
#             )
#         except ValidationError as exc:
#             messages.error(request, str(exc))
#         else:
#             messages.success(
#                 request,
#                 f"Deployment of {deployment.staff.full_name} at "
#                 f"{deployment.company.name} has been ended.",
#             )
#         return redirect("organization:deployment-list")


# class OrganizationExportView(LoginRequiredMixin, PermissionRequiredMixin, View):
#     """Downloads the full client organization list as CSV."""

#     permission_required = "organization.view_company"

#     def get(self, request):
#         queryset = Company.objects.filter(is_active=True).order_by("name")
#         fields = [
#             ("Code", "code"),
#             ("Name", "name"),
#             ("Industry", "industry"),
#             ("Contact Person", "contact_person"),
#             ("Phone", "phone"),
#             ("Email", "email"),
#             ("Address", "address"),
#             ("Contract Start", lambda c: c.contract_start_date or ""),
#             ("Contract End", lambda c: c.contract_end_date or ""),
#             ("Status", "status"),
#         ]
#         return export_queryset_as_csv(queryset, fields, "client_organizations.csv")


# class DeploymentExportView(LoginRequiredMixin, PermissionRequiredMixin, View):
#     """Downloads every current staff posting/location as CSV."""

#     permission_required = "organization.view_staffdeployment"

#     def get(self, request):
#         queryset = StaffDeployment.objects.current().order_by(
#             "company__name", "staff__user__last_name"
#         )
#         fields = [
#             ("Employee No", lambda d: d.staff.employee_no),
#             ("Staff Name", lambda d: d.staff.full_name),
#             ("Organization", lambda d: d.company.name),
#             ("Department", lambda d: d.department.name),
#             ("Designation", lambda d: d.designation.name),
#             ("Location", lambda d: d.location),
#             ("Posted Since", lambda d: d.start_date),
#         ]
#         return export_queryset_as_csv(queryset, fields, "staff_deployments.csv")



from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, ListView

from employees.models import Staff

from core.exports import export_queryset_as_csv

from .forms import StaffDeploymentForm
from .models import Company, Department, OrganizationStatus, StaffDeployment
from .services import deploy_staff, end_deployment


class DeploymentListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """
    Admin-facing view of every staff member's current posting and
    location. This is the primary "where is everyone right now"
    screen for HR, branch managers and auditors.

    Filtering/search happen server-side via GET params so the result
    is bookmarkable/shareable and works with JavaScript disabled.
    """

    model = StaffDeployment
    template_name = "organization/deployment_list.html"
    context_object_name = "deployments"
    paginate_by = 25
    permission_required = "organization.view_staffdeployment"

    def get_queryset(self):
        qs = StaffDeployment.objects.current()

        company_id = self.request.GET.get("company")
        department_id = self.request.GET.get("department")
        search_term = self.request.GET.get("q", "")

        if company_id:
            qs = qs.for_company(company_id)
        if department_id:
            qs = qs.for_department(department_id)
        if search_term:
            qs = qs.search(search_term)

        return qs.order_by("company__name", "staff__user__last_name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        current_qs = StaffDeployment.objects.current()
        deployed_staff_ids = current_qs.values_list("staff_id", flat=True)

        context["companies"] = Company.objects.order_by("name")
        context["departments"] = Department.objects.order_by("name")
        context["selected_company"] = self.request.GET.get("company", "")
        context["selected_department"] = self.request.GET.get("department", "")
        context["search_term"] = self.request.GET.get("q", "")

        context["stats"] = {
            "total_deployed": current_qs.count(),
            "total_companies": current_qs.values("company").distinct().count(),
            "total_departments": current_qs.values("department").distinct().count(),
            "unassigned_staff": Staff.objects.filter(is_active=True)
            .exclude(id__in=deployed_staff_ids)
            .count(),
        }
        return context


class DeploymentCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Deploys or redeploys a staff member. Deliberately does NOT call
    ModelForm.save() — the actual write goes through
    organization.services.deploy_staff() so the close-previous /
    open-new transaction and validation rules are always applied,
    regardless of how many places in the codebase end up calling this.
    """

    form_class = StaffDeploymentForm
    template_name = "organization/deployment_form.html"
    permission_required = "organization.add_staffdeployment"
    success_url = reverse_lazy("organization:deployment-list")

    def form_valid(self, form):
        try:
            result = deploy_staff(
                staff=form.cleaned_data["staff"],
                company=form.cleaned_data["company"],
                department=form.cleaned_data["department"],
                designation=form.cleaned_data["designation"],
                start_date=form.cleaned_data["start_date"],
                performed_by=self.request.user,
            )
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)

        if result.previous_deployment:
            messages.success(
                self.request,
                f"{result.deployment.staff.full_name} redeployed to "
                f"{result.deployment.company.name}. Previous posting closed "
                f"and kept in history.",
            )
        else:
            messages.success(
                self.request,
                f"{result.deployment.staff.full_name} deployed to "
                f"{result.deployment.company.name}.",
            )
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_create"] = True
        return context


class DeploymentHistoryView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """
    Full, immutable posting history for a single staff member —
    every past and present deployment, oldest actions never edited
    or removed.
    """

    model = StaffDeployment
    template_name = "organization/deployment_history.html"
    context_object_name = "deployments"
    permission_required = "organization.view_staffdeployment"

    def get_queryset(self):
        self.staff = get_object_or_404(Staff, pk=self.kwargs["staff_id"])
        return StaffDeployment.objects.filter(staff=self.staff).order_by("-start_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["staff"] = self.staff
        return context


class EndDeploymentView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    Closes a current deployment without opening a new one (e.g. staff
    pulled off a client site, awaiting a new posting). POST-only.
    """

    permission_required = "organization.change_staffdeployment"

    def post(self, request, pk):
        deployment = get_object_or_404(StaffDeployment, pk=pk, is_current=True)
        try:
            end_deployment(
                deployment=deployment,
                end_date=timezone.localdate(),
                performed_by=request.user,
            )
        except ValidationError as exc:
            messages.error(request, str(exc))
        else:
            messages.success(
                request,
                f"Deployment of {deployment.staff.full_name} at "
                f"{deployment.company.name} has been ended.",
            )
        return redirect("organization:deployment-list")


def _companies_with_deployed_count():
    """
    Shared base queryset: every active organization annotated with a
    live count of currently-deployed staff, computed as a single
    conditional aggregate rather than one query per row. Reused by
    the list view, the print view, and the CSV export so the three
    "how many staff at each client" numbers are always identical —
    computed once, not redefined three different ways.
    """
    return Company.objects.filter(is_active=True).annotate(
        deployed_staff_count=Count(
            "deployments", filter=Q(deployments__is_current=True), distinct=True
        )
    )


class OrganizationListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """
    Admin-facing list of every client organization — contact info,
    contract status, and a live count of staff currently deployed
    there. This is the "who are our clients and how many people do
    we have at each one" screen.
    """

    model = Company
    template_name = "organization/organization_list.html"
    context_object_name = "organizations"
    paginate_by = 20
    permission_required = "organization.view_company"

    def get_queryset(self):
        qs = _companies_with_deployed_count()

        status = self.request.GET.get("status", "")
        search = self.request.GET.get("q", "").strip()

        if status:
            qs = qs.filter(status=status)
        if search:
            qs = qs.filter(
                Q(name__icontains=search)
                | Q(code__icontains=search)
                | Q(contact_person__icontains=search)
                | Q(industry__icontains=search)
            )
        return qs.order_by("name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()

        context["status_choices"] = OrganizationStatus.choices
        context["selected_status"] = self.request.GET.get("status", "")
        context["search_term"] = self.request.GET.get("q", "")

        context["stats"] = {
            "total_organizations": Company.objects.filter(is_active=True).count(),
            "active_organizations": Company.objects.filter(
                is_active=True, status=OrganizationStatus.ACTIVE
            ).count(),
            "total_deployed_staff": StaffDeployment.objects.current().count(),
            "contracts_expiring_soon": Company.objects.filter(
                is_active=True,
                contract_end_date__isnull=False,
                contract_end_date__gte=today,
                contract_end_date__lte=today + timedelta(days=30),
            ).count(),
        }
        return context


class OrganizationPrintView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """
    Print/PDF-ready version of the organization list — full list (no
    pagination), A4-optimized layout, no sidebar.

    Deliberately does NOT use a PDF-generation library (WeasyPrint,
    xhtml2pdf, ReportLab, ...): those need system-level dependencies
    that are unreliable on PythonAnywhere Free and shared cPanel
    hosting. The browser's own "Print > Save as PDF" is the PDF
    engine here — zero extra dependencies, works identically on
    every host in the spec.
    """

    model = Company
    template_name = "organization/organization_print.html"
    context_object_name = "organizations"
    permission_required = "organization.view_company"

    def get_queryset(self):
        return _companies_with_deployed_count().order_by("name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["generated_at"] = timezone.now()
        context["generated_by"] = self.request.user
        return context


class OrganizationExportView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Downloads the full client organization list as CSV, including
    each organization's live deployed-staff count."""

    permission_required = "organization.view_company"

    def get(self, request):
        queryset = _companies_with_deployed_count().order_by("name")
        fields = [
            ("Code", "code"),
            ("Name", "name"),
            ("Industry", "industry"),
            ("Contact Person", "contact_person"),
            ("Phone", "phone"),
            ("Email", "email"),
            ("Address", "address"),
            ("Deployed Staff", "deployed_staff_count"),
            ("Contract Start", lambda c: c.contract_start_date or ""),
            ("Contract End", lambda c: c.contract_end_date or ""),
            ("Status", "status"),
        ]
        return export_queryset_as_csv(queryset, fields, "client_organizations.csv")


class DeploymentExportView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Downloads every current staff posting/location as CSV."""

    permission_required = "organization.view_staffdeployment"

    def get(self, request):
        queryset = StaffDeployment.objects.current().order_by(
            "company__name", "staff__user__last_name"
        )
        fields = [
            ("Employee No", lambda d: d.staff.employee_no),
            ("Staff Name", lambda d: d.staff.full_name),
            ("Organization", lambda d: d.company.name),
            ("Department", lambda d: d.department.name),
            ("Designation", lambda d: d.designation.name),
            ("Location", lambda d: d.location),
            ("Posted Since", lambda d: d.start_date),
        ]
        return export_queryset_as_csv(queryset, fields, "staff_deployments.csv")