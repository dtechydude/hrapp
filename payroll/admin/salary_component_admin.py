from django.contrib import admin

from payroll.models import SalaryComponent


@admin.register(SalaryComponent)
class SalaryComponentAdmin(admin.ModelAdmin):

    list_display = (

        "code",

        "name",

        "component_type",

        "calculation_method",

        "default_amount",

        "percentage",

        "display_order",

        "is_active",

        "is_system",

    )

    list_filter = (

        "component_type",

        "calculation_method",

        "is_active",

        "is_system",

    )

    search_fields = (

        "code",

        "name",

    )

    ordering = (

        "display_order",

        "component_type",

        "name",

    )

    list_per_page = 50

    save_on_top = True

    list_editable = (

        "display_order",

        "is_active",

    )

    readonly_fields = (

        "uuid",

        "created_at",

        "updated_at",

    )

    fieldsets = (

        (

            "Component",

            {

                "fields": (

                    "uuid",

                    "code",

                    "name",

                    "component_type",

                    "description",

                )

            },

        ),

        (

            "Calculation",

            {

                "fields": (

                    "calculation_method",

                    "default_amount",

                    "percentage",

                    "formula",

                )

            },

        ),

        (

            "Behaviour",

            {

                "fields": (

                    "affects_gross",

                    "affects_net",

                    "is_taxable",

                    "is_pensionable",

                    "is_statutory",

                    "is_proratable",

                    "show_on_payslip",

                    "is_editable",

                    "is_system",

                    "display_order",

                    "is_active",

                )

            },

        ),

        (

            "Audit",

            {

                "classes": ("collapse",),

                "fields": (

                    "created_by",

                    "updated_by",

                    "created_at",

                    "updated_at",

                )

            },

        ),

    )