from django.db import models
from django.db.models import Q


class StaffDeploymentQuerySet(models.QuerySet):
    """
    Reusable, chainable query building blocks for StaffDeployment.

    Kept here (instead of duplicated ad-hoc filters inside views) so
    the dashboard, this list screen, a future REST API, and reports
    all resolve "who is currently deployed where" the exact same way.
    """

    def with_related(self):
        """Avoids N+1 queries when rendering staff name, organization,
        department and designation on a list page."""
        return self.select_related(
            "staff",
            "staff__user",
            "staff__staff_rank",
            "company",
            "department",
            "designation",
        )

    def current(self):
        """Only postings that are presently active."""
        return self.filter(is_current=True, is_active=True)

    def for_company(self, company_id):
        return self.filter(company_id=company_id)

    def for_department(self, department_id):
        return self.filter(department_id=department_id)

    def search(self, term: str):
        """
        Free-text search across staff name/employee number and the
        client organization name — the fields an HR user is most
        likely to type into a single search box.
        """
        term = (term or "").strip()
        if not term:
            return self
        return self.filter(
            Q(staff__employee_no__icontains=term)
            | Q(staff__user__first_name__icontains=term)
            | Q(staff__user__last_name__icontains=term)
            | Q(company__name__icontains=term)
        )


class StaffDeploymentManager(models.Manager.from_queryset(StaffDeploymentQuerySet)):
    """
    Applies with_related() by default so callers get a safe query
    even if they forget to call it explicitly. Chaining .current(),
    .search(), etc. on the default manager still works because they
    all return querysets of the same class.
    """

    def get_queryset(self):
        return super().get_queryset().with_related()
