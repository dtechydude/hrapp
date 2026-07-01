from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Company,
    Department,
    StaffRole,
    StaffRank,
    StaffDeployment,
)


# ==========================================================
# Base Admin (Shared by lookup tables)
# ==========================================================

class BaseLookupAdmin(admin.ModelAdmin):
    list_per_page = 30
    ordering = ("name",)

    list_display = (
        "name",
        "description_short",
        "slug",
    )

    search_fields = (
        "name",
        "description",
    )

    readonly_fields = (
        "slug",
    )

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "description",
                )
            },
        ),
        (
            "System Information",
            {
                "classes": ("collapse",),
                "fields": (
                    "slug",
                ),
            },
        ),
    )

    def description_short(self, obj):
        if obj.description:
            return obj.description[:60]
        return "-"

    description_short.short_description = "Description"


# ==========================================================
# Company
# ==========================================================

@admin.register(Company)
class CompanyAdmin(BaseLookupAdmin):
    pass


# ==========================================================
# Department
# ==========================================================

@admin.register(Department)
class DepartmentAdmin(BaseLookupAdmin):
    pass


# ==========================================================
# Staff Role
# ==========================================================

@admin.register(StaffRole)
class StaffRoleAdmin(BaseLookupAdmin):
    pass


# ==========================================================
# Staff Rank
# ==========================================================

@admin.register(StaffRank)
class StaffRankAdmin(BaseLookupAdmin):
    pass


# ==========================================================
# Staff Deployment
# ==========================================================

@admin.register(StaffDeployment)
class StaffDeploymentAdmin(admin.ModelAdmin):

    list_per_page = 50

    date_hierarchy = "start_date"

    autocomplete_fields = (
        "staff",
        "company",
        "department",
        "designation",
    )

    list_select_related = (
        "staff",
        "company",
        "department",
        "designation",
    )

    ordering = (
        "-is_current",
        "-start_date",
    )

    list_display = (
        "staff",
        "company",
        "department",
        "designation",
        "start_date",
        "end_date",
        "status_badge",
    )

    list_filter = (
        "is_current",
        "company",
        "department",
        "designation",
        "start_date",
    )

    search_fields = (
        "staff__first_name",
        "staff__last_name",
        "staff__staff_id",
        "company__name",
        "department__name",
        "designation__name",
    )

    fieldsets = (
        (
            "Deployment Information",
            {
                "fields": (
                    "staff",
                    "company",
                    "department",
                    "designation",
                )
            },
        ),
        (
            "Deployment Period",
            {
                "fields": (
                    "start_date",
                    "end_date",
                    "is_current",
                )
            },
        ),
    )

    actions = (
        "mark_current",
        "mark_inactive",
    )

    # -----------------------------------------
    # Status Badge
    # -----------------------------------------

    @admin.display(description="Status")
    def status_badge(self, obj):

        if obj.is_current:
            return format_html(
                '<span style="color:white; background:#198754; padding:3px 10px; border-radius:10px;">Current</span>'
            )

        return format_html(
            '<span style="color:white; background:#dc3545; padding:3px 10px; border-radius:10px;">Ended</span>'
        )

    # -----------------------------------------
    # Bulk Actions
    # -----------------------------------------

    @admin.action(description="Mark selected deployments as Current")
    def mark_current(self, request, queryset):
        queryset.update(is_current=True)

    @admin.action(description="Mark selected deployments as Ended")
    def mark_inactive(self, request, queryset):
        queryset.update(is_current=False)