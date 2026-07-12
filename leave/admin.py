"""
leave/admin.py
───────────────────────────────────────────────────────────────────────────
LeaveType is admin-managed (HR adds/edits leave categories here — no code
deploy needed). LeaveBalance and LeaveRequest are visible for support/
audit purposes; day-to-day approve/decline happens through the app UI
(leave/views.py), not the admin.
───────────────────────────────────────────────────────────────────────────
"""
from django.contrib import admin

from .models import LeaveBalance, LeaveRequest, LeaveType


@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "default_entitlement_days", "requires_note", "is_active")
    list_filter = ("is_active", "requires_note")
    search_fields = ("name", "code")
    prepopulated_fields = {"code": ("name",)}


@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ("staff", "leave_type", "year", "entitled_days", "used_days", "remaining_days")
    list_filter = ("leave_type", "year")
    search_fields = ("staff__user__first_name", "staff__user__last_name", "staff__employee_no")
    autocomplete_fields = ("staff", "leave_type")

    def remaining_days(self, obj):
        return obj.remaining_days
    remaining_days.short_description = "Remaining"


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ("staff", "leave_type", "start_date", "end_date", "days_requested", "status", "applied_at")
    list_filter = ("status", "leave_type")
    search_fields = ("staff__user__first_name", "staff__user__last_name", "staff__employee_no")
    autocomplete_fields = ("staff", "leave_type")
    readonly_fields = ("uuid", "days_requested", "applied_at", "reviewed_by", "reviewed_at")
    date_hierarchy = "applied_at"
