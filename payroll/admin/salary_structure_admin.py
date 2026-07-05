from django.contrib import admin

from payroll.models.salary_structure import (
    SalaryStructure,
    SalaryStructureItem,
)


class SalaryStructureItemInline(admin.TabularInline):

    model = SalaryStructureItem

    extra = 0


@admin.register(SalaryStructure)
class SalaryStructureAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "company",
        "is_active",
    )

    list_filter = (
        "company",
        "is_active",
    )

    search_fields = (
        "name",
    )

    inlines = [
        SalaryStructureItemInline,
    ]

    readonly_fields = (
        "uuid",
        "created_at",
        "updated_at",
    )