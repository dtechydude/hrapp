"""
employees/exports.py

Kept in its own file rather than appended to your existing
employees/views.py, since that file wasn't shared with me and I
don't want to risk overwriting anything already in it. Wire the URL
in employees/urls.py per the one-line snippet in this module's
docstring below.
"""
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views import View

from core.exports import export_queryset_as_csv

from .models import Staff


class StaffExportView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    Downloads the full active staff list as CSV.

    Add to employees/urls.py:
        from .exports import StaffExportView
        path("export/", StaffExportView.as_view(), name="staff-export"),
    """

    permission_required = "employees.view_staff"

    def get(self, request):
        queryset = (
            Staff.objects.filter(is_active=True)
            .select_related("user", "staff_rank")
            .order_by("user__last_name", "user__first_name")
        )
        fields = [
            ("Employee No", "employee_no"),
            ("Full Name", lambda s: s.full_name),
            ("Gender", "gender"),
            ("Phone", "phone_mobile"),
            ("Employment Type", "employment_type"),
            ("Employment Status", "employment_status"),
            ("Date Employed", "date_employed"),
            ("Rank", lambda s: s.staff_rank.name if s.staff_rank else ""),
        ]
        return export_queryset_as_csv(queryset, fields, "staff_list.csv")