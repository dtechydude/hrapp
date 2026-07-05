from django.contrib import messages
from django.utils import timezone


def approve_payroll(modeladmin, request, queryset):

    count = 0

    for payroll in queryset:

        if not payroll.approved_at:

            payroll.approved_by = request.user
            payroll.approved_at = timezone.now()

            payroll.save()

            count += 1

    modeladmin.message_user(
        request,
        f"{count} payroll(s) approved.",
        messages.SUCCESS,
    )


approve_payroll.short_description = "Approve selected Payroll"


def lock_period(modeladmin, request, queryset):

    updated = queryset.update(locked=True)

    modeladmin.message_user(
        request,
        f"{updated} Payroll Period(s) locked.",
        messages.SUCCESS,
    )


lock_period.short_description = "Lock Payroll Period"


def unlock_period(modeladmin, request, queryset):

    updated = queryset.update(locked=False)

    modeladmin.message_user(
        request,
        f"{updated} Payroll Period(s) unlocked.",
        messages.SUCCESS,
    )


unlock_period.short_description = "Unlock Payroll Period"