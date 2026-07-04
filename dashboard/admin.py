from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html

from .models import CorporateIdentity


@admin.register(CorporateIdentity)
class CorporateIdentityAdmin(admin.ModelAdmin):
    """
    Administration for the company's branding.

    HRPAMS supports only ONE Corporate Identity.
    """

    list_display = (
        "name",
        "is_default",
        "phone",
        "email",
        "logo_preview",
        "updated_at",
    )

    list_display_links = ("name",)

    list_filter = (
        "is_default",
    )

    search_fields = (
        "name",
        "email",
        "phone",
        "rc_number",
    )

    readonly_fields = (
        "slug",
        "created_at",
        "updated_at",
        "logo_preview",
        "signature_preview",
    )

    fieldsets = (
        (
            "Corporate Information",
            {
                "fields": (
                    "name",
                    "identity_label",
                    "is_default",
                    "slug",
                )
            },
        ),
        (
            "Contact Information",
            {
                "fields": (
                    "address",
                    "address_line_2",
                    "phone",
                    "phone_2",
                    "email",
                    "website",
                    "rc_number",
                )
            },
        ),
        (
            "Brand Assets",
            {
                "fields": (
                    "logo",
                    "logo_preview",
                    "signature",
                    "signature_preview",
                    "signatory_name",
                    "signatory_title",
                )
            },
        ),
        (
            "Document Theme",
            {
                "description": (
                    "These colours are used on ID Cards, Payslips and "
                    "other generated documents."
                ),
                "fields": (
                    "primary_colour",
                    "accent_colour",
                ),
            },
        ),
        (
            "System Information",
            {
                "classes": ("collapse",),
                "fields": (
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )

    #
    # Image previews
    #

    @admin.display(description="Logo")
    def logo_preview(self, obj):
        if obj.logo:
            return format_html(
                '<img src="{}" style="height:55px;border-radius:6px;border:1px solid #ddd;" />',
                obj.logo.url,
            )
        return "-"

    @admin.display(description="Signature")
    def signature_preview(self, obj):
        if obj.signature:
            return format_html(
                '<img src="{}" style="height:45px;border-radius:6px;border:1px solid #ddd;" />',
                obj.signature.url,
            )
        return "-"

    #
    # Restrict to ONE Corporate Identity
    #

    def has_add_permission(self, request):
        """
        Prevent creation of more than one record.
        """
        return CorporateIdentity.objects.count() == 0

    #
    # Friendly message instead of Add button
    #

    def changelist_view(self, request, extra_context=None):

        if CorporateIdentity.objects.exists():
            self.message_user(
                request,
                "Only one Corporate Identity is permitted. "
                "Edit the existing record to update company information.",
                level=messages.INFO,
            )

        return super().changelist_view(
            request,
            extra_context=extra_context,
        )