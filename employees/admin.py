from django.contrib import admin
from django.utils.html import format_html

from .models import Staff, StaffAttendance
from organization.models import StaffDeployment


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    """
    Enterprise HR Staff Administration
    """

    list_display = (
        "photo",
        "employee_no",
        "full_name_display",
        "gender",
        "employment_status",
        "current_company",
        "current_department",
        "current_role",
        "phone_mobile",
        "date_employed",
        "is_active",
    )

    list_display_links = (
        "employee_no",
        "full_name_display",
    )

    list_filter = (
        "employment_status",
        "employment_type",
        "gender",
        "staff_rank",
        "is_active",
        "date_employed",
    )

    search_fields = (
        "employee_no",
        "user__username",
        "user__first_name",
        "user__last_name",
        "middle_name",
        "phone_mobile",
        "official_email",
        "personal_email",
    )

    readonly_fields = (
        "uuid",
        "employee_no",
        "age",
        "created",
        "updated",
        "created_by",
        "updated_by",
    )

    date_hierarchy = "date_employed"

    ordering = (
        "user__last_name",
        "user__first_name",
    )

    list_per_page = 50

    save_on_top = True

    fieldsets = (

        (
            "Employee Information",
            {
                "fields": (
                    "uuid",
                    "employee_no",
                    "user",
                    "middle_name",
                    "gender",
                    "date_of_birth",
                    "age",
                    "state_of_origin",
                    "nationality",
                    "marital_status",
                )
            },
        ),

        (
            "Employment",
            {
                "fields": (
                    "employment_type",
                    "employment_status",
                    "staff_rank",
                    "date_employed",
                    "confirmation_date",
                )
            },
        ),

        (
            "Contact Information",
            {
                "fields": (
                    "phone_mobile",
                    "phone_home",
                    "official_email",
                    "personal_email",
                    "address",
                )
            },
        ),

        (
            "Academic Information",
            {
                "classes": ("collapse",),
                "fields": (
                    "qualification",
                    "graduation_year",
                    "institution",
                    "professional_body",
                ),
            },
        ),

        (
            "Guarantor",
            {
                "classes": ("collapse",),
                "fields": (
                    "guarantor_name",
                    "guarantor_phone",
                    "guarantor_email",
                    "guarantor_address",
                ),
            },
        ),

        (
            "Next of Kin",
            {
                "classes": ("collapse",),
                "fields": (
                    "next_of_kin_name",
                    "next_of_kin_phone",
                    "next_of_kin_address",
                ),
            },
        ),

        (
            "Notes",
            {
                "classes": ("collapse",),
                "fields": (
                    "notes",
                ),
            },
        ),

        (
            "Audit Trail",
            {
                "classes": ("collapse",),
                "fields": (
                    "is_active",
                    "created",
                    "updated",
                    "created_by",
                    "updated_by",
                ),
            },
        ),
    )

    ##########################################################

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        return qs.select_related(
            "user",
            "staff_rank",
            "user__profile",
        )
        

    ##########################################################

    @admin.display(description="Photo")
    def photo(self, obj):

        if hasattr(obj.user, "profile") and obj.user.profile.image:
            return format_html(
                '<img src="{}" width="45" height="45" style="border-radius:50%;" />',
                obj.user.profile.image.url,
            )

        return "-"

    ##########################################################

    @admin.display(description="Full Name", ordering="user__last_name")
    def full_name_display(self, obj):
        return obj.full_name

    ##########################################################

    @admin.display(description="Age")
    def age(self, obj):
        return obj.age

    ##########################################################

    @admin.display(description="Company")
    def current_company(self, obj):

        deployment = obj.current_deployment

        if deployment:
            return deployment.company

        return "-"

    ##########################################################

    @admin.display(description="Department")
    def current_department(self, obj):

        deployment = obj.current_deployment

        if deployment:
            return deployment.department

        return "-"

    ##########################################################

    @admin.display(description="Role")
    def current_role(self, obj):

        deployment = obj.current_deployment

        if deployment:
            return deployment.designation.name

        return "-"

@admin.register(StaffAttendance)
class StaffAttendanceAdmin(admin.ModelAdmin):

    list_display = (
        "employee",
        "date",
        "check_in_time",
        "check_out_time",
        "status",
        "is_late",
        "work_duration",
    )

    list_filter = (
        "status",
        "is_late",
        "date",
    )

    search_fields = (
        "employee__employee_no",
        "employee__user__first_name",
        "employee__user__last_name",
    )

    ordering = (
        "-date",
    )

    readonly_fields = (
        "work_duration",
        "created_at",
    )

    date_hierarchy = "date"

    list_per_page = 100



"""
idcards/admin.py
───────────────────────────────────────────────────────────────────────────
Django admin registration for StaffIDCard and its reissue history.
Hard delete is intentionally not exposed anywhere in the portal UI (see
views.py) — the admin is the only place a card row can be removed, and
even here the reissue log is kept read-only to preserve history.
───────────────────────────────────────────────────────────────────────────
"""
from django.contrib import admin

from .models import IDCardReissueLog, StaffIDCard


class ReissueLogInline(admin.TabularInline):
    model = IDCardReissueLog
    extra = 0
    readonly_fields = (
        "previous_card_number",
        "new_card_number",
        "reason",
        "action",
        "performed_by",
        "performed_at",
    )
    can_delete = False
    max_num = 0  # display-only; new rows are created by services.py


@admin.register(StaffIDCard)
class StaffIDCardAdmin(admin.ModelAdmin):
    list_display = (
        "card_number",
        "staff",
        "status",
        "issue_date",
        "expiry_date",
        "is_printed",
        "print_count",
    )
    list_filter = ("status", "is_printed", "issue_date")
    search_fields = (
        "card_number",
        "staff__user__first_name",
        "staff__user__last_name",
        "staff__employee_no",
    )
    readonly_fields = (
        "uuid",
        "card_number",
        "qr_code",
        "print_count",
        "last_printed_at",
        "created_at",
        "updated_at",
    )
    autocomplete_fields = ("staff",)
    inlines = [ReissueLogInline]


@admin.register(IDCardReissueLog)
class IDCardReissueLogAdmin(admin.ModelAdmin):
    list_display = ("card", "action", "previous_card_number", "new_card_number", "performed_by", "performed_at")
    list_filter = ("action",)
    search_fields = ("card__card_number", "previous_card_number", "new_card_number")

    def has_add_permission(self, request):
        return False  # rows are only ever created via IDCardService

    def has_change_permission(self, request, obj=None):
        return False
