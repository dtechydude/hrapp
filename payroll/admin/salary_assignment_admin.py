from django.contrib import admin

from payroll.models.salary_assignment import SalaryAssignment


@admin.register(SalaryAssignment)
class SalaryAssignmentAdmin(admin.ModelAdmin):

    list_display = (
        "staff",
        "salary_structure",
        # "basic_salary",
        # "effective_date",
        # "is_active",
    )

    list_filter = (
        # "is_active",
    )

    search_fields = (
        "staff__user__first_name",
        "staff__user__last_name",
        "staff__employee_no",
    )

    autocomplete_fields = (
        "staff",
        "salary_structure",
    )

    readonly_fields = (
        "uuid",
        "created_at",
        "updated_at",
    )