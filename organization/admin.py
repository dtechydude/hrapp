from django.contrib import admin

from .models import Company, Department, StaffDeployment, StaffRank, StaffRole


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "name",
        "industry",
        "contact_person",
        "phone",
        "status",
        "contract_end_date",
        "is_active",
    )
    list_filter = ("status", "industry", "is_active")
    search_fields = ("code", "name", "contact_person", "email", "phone")
    readonly_fields = ("code", "slug", "created_at", "updated_at", "created_by", "updated_by")
    fieldsets = (
        ("Identity", {"fields": ("name", "code", "industry", "logo", "description")}),
        ("Contact", {"fields": ("address", "contact_person", "phone", "email")}),
        ("Contract", {"fields": ("contract_start_date", "contract_end_date", "status")}),
        ("Notes", {"fields": ("notes",)}),
        (
            "Audit",
            {
                "classes": ("collapse",),
                "fields": ("is_active", "created_at", "updated_at", "created_by", "updated_by"),
            },
        ),
    )


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(StaffRole)
class StaffRoleAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(StaffRank)
class StaffRankAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(StaffDeployment)
class StaffDeploymentAdmin(admin.ModelAdmin):
    list_display = (
        "staff",
        "company",
        "department",
        "designation",
        "start_date",
        "end_date",
        "is_current",
    )
    list_filter = ("is_current", "company", "department")
    search_fields = (
        "staff__employee_no",
        "staff__user__first_name",
        "staff__user__last_name",
        "company__name",
    )
    autocomplete_fields = ("staff", "company", "department", "designation")
    date_hierarchy = "start_date"
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")