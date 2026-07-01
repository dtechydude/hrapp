from __future__ import annotations

import logging
import os

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.utils.html import format_html

from import_export import resources
from import_export.admin import ImportExportModelAdmin

from users.models import Profile

# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------

User = get_user_model()

logger = logging.getLogger(__name__)

DEFAULT_PROFILE_IMAGE = "default.jpg"


# -----------------------------------------------------------------------------
# USER IMPORT / EXPORT RESOURCE
# -----------------------------------------------------------------------------

class UserResource(resources.ModelResource):
    """
    Import / Export configuration for Django Users.
    """

    class Meta:
        model = User

        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_staff",
            "is_superuser",
            "is_active",
            "date_joined",
            "last_login",
        )

        export_order = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_staff",
            "is_superuser",
            "is_active",
            "date_joined",
            "last_login",
        )

class ProfileResource(resources.ModelResource):
    class Meta:
        model = Profile

        fields = (
            "user__username",
            "user__first_name",
            "user__last_name",
            "user__email",
            "phone",
            "coloured_role",
            "state_of_origin",
            "is_active",
            "referral_code",
            "created",
        )

        export_order = fields

# -----------------------------------------------------------------------------
# IMAGE UTILITIES
# -----------------------------------------------------------------------------

def delete_old_profile_image(old_image, new_image):
    """
    Deletes the previous profile picture whenever a new one
    replaces it.

    Safe because it:

    • never deletes default.jpg
    • never raises an exception
    • ignores missing files
    """

    if not old_image:
        return

    old_name = str(old_image)

    new_name = str(new_image) if new_image else ""

    if old_name == new_name:
        return

    if os.path.basename(old_name) == DEFAULT_PROFILE_IMAGE:
        return

    try:

        old_path = old_image.path

        if os.path.isfile(old_path):

            os.remove(old_path)

            logger.info(
                "Deleted old profile image: %s",
                old_path,
            )

    except (ValueError, AttributeError):
        pass

    except OSError as e:

        logger.warning(
            "Unable to delete image %s (%s)",
            old_name,
            e,
        )


# -----------------------------------------------------------------------------
# IMAGE DISPLAY HELPERS
# -----------------------------------------------------------------------------

def profile_thumbnail(obj):
    """
    Small circular thumbnail for Django list display.
    """

    if obj.image:

        try:

            return format_html(
                """
                <img src="{}"
                     style="
                        width:45px;
                        height:45px;
                        border-radius:50%;
                        object-fit:cover;
                        border:2px solid #ddd;
                     ">
                """,
                obj.image.url,
            )

        except Exception:
            pass

    return format_html(
        """
        <div style="
            width:45px;
            height:45px;
            border-radius:50%;
            background:#efefef;
            display:flex;
            align-items:center;
            justify-content:center;
            color:#888;
            font-size:11px;">
            N/A
        </div>
        """
    )


profile_thumbnail.short_description = "Photo"


# -----------------------------------------------------------------------------
# USER ADMIN
# -----------------------------------------------------------------------------

try:
    admin.site.unregister(User)

except admin.sites.NotRegistered:
    pass



# ── Inline: edit Profile directly from the User admin page ───────────────────
# =============================================================================
# PROFILE INLINE
# =============================================================================

class ProfileInline(admin.StackedInline):
    model = Profile
    fk_name = "user"   # <-- This is the fix

    extra = 0
    can_delete = False

    verbose_name = "Profile"
    verbose_name_plural = "Profile"

    fields = (
        "image",
        "phone",
        "user_type",
        "state_of_origin",
        "address",
        "bio",
        "is_active",
    )

    def save_formset(self, request, form, formset, change):
        """
        Delete previous image whenever user uploads a replacement.
        """

        instances = formset.save(commit=False)

        for instance in instances:

            if instance.pk:

                try:
                    old = Profile.objects.get(pk=instance.pk)

                    delete_old_profile_image(
                        old.image,
                        instance.image,
                    )

                except Profile.DoesNotExist:
                    pass

            instance.save()

        formset.save_m2m()


@admin.register(User)
class UserAdmin(DefaultUserAdmin, ImportExportModelAdmin):

    resource_class = UserResource

    inlines = (ProfileInline,)

    list_display = (
        "username",
        "first_name",
        "last_name",
        "email",
        "is_staff",
        "is_active",
        "date_joined",
    )

    list_filter = (
        "is_staff",
        "is_superuser",
        "is_active",
    )

    search_fields = (
        "username",
        "first_name",
        "last_name",
        "email",
    )

    ordering = (
        "last_name",
        "first_name",
    )


# =============================================================================
# PROFILE ADMIN
# =============================================================================

@admin.register(Profile)
class ProfileAdmin(ImportExportModelAdmin):
    resource_class = ProfileResource

    list_per_page = 50

    ordering = (
        "user_type",
        "user__last_name",
        "user__first_name",
    )

    actions = (
        "activate_profiles",
        "deactivate_profiles",
    )

    list_display = (
        "photo",
        "get_username",
        "get_full_name",
        "user_type",
        "phone",
        "state_of_origin",
        "is_active",
        "has_photo",
        "created",
    )

    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "user__email",
        "phone",
        "referral_code",
    )

    list_filter = (
        "user_type",
        "state_of_origin",
        "is_active",
        "created",
        ("user__date_joined", admin.DateFieldListFilter),
    )

    readonly_fields = (
        "uuid",
        "referral_code",
        "created",
        "updated",
        "image_preview",
    )

    fieldsets = (

        (
            "User Account",
            {
                "fields": (
                    "user",
                    "user_type",
                    "is_active",
                )
            },
        ),

        (
            "Profile Photo",
            {
                "fields": (
                    "image_preview",
                    "image",
                ),
                "description":
                    "Uploading another picture automatically "
                    "removes the previous image from the server.",
            },
        ),

        (
            "Personal Information",
            {
                "fields": (
                    "phone",
                    "state_of_origin",
                    "address",
                    "bio",
                )
            },
        ),

        (
            "Referral Information",
            {
                "fields": (
                    "referral_code",
                    "recommended_by",
                )
            },
        ),

        (
            "System Information",
            {
                "fields": (
                    "uuid",
                    "created",
                    "updated",
                ),
                "classes": (
                    "collapse",
                ),
            },
        ),
    )

    # -------------------------------------------------------------------------
    # PERFORMANCE
    # -------------------------------------------------------------------------

    def get_queryset(self, request):

        return (
            super()
            .get_queryset(request)
            .select_related("user")
        )

    # -------------------------------------------------------------------------
    # LIST DISPLAY
    # -------------------------------------------------------------------------

    @admin.display(description="Photo")
    def photo(self, obj):

        return profile_thumbnail(obj)

    @admin.display(
        description="Username",
        ordering="user__username",
    )
    def get_username(self, obj):

        return obj.user.username

    @admin.display(
        description="Full Name",
        ordering="user__last_name",
    )
    def get_full_name(self, obj):

        return obj.full_name

    @admin.display(
        boolean=True,
        description="Custom Photo",
    )
    def has_photo(self, obj):

        if not obj.image:
            return False

        return (
            os.path.basename(
                str(obj.image)
            ) != DEFAULT_PROFILE_IMAGE
        )

    # -------------------------------------------------------------------------
    # IMAGE PREVIEW
    # -------------------------------------------------------------------------

    @admin.display(description="Current Photo")
    def image_preview(self, obj):

        if obj.image:

            try:

                return format_html(
                    """
                    <img src="{}"
                    style="
                        width:130px;
                        height:130px;
                        border-radius:8px;
                        object-fit:cover;
                        border:3px solid #ddd;
                    ">
                    """,
                    obj.image.url,
                )

            except Exception:
                pass

        return format_html(
            """
            <span style="color:#999;">
            No Image Uploaded
            </span>
            """
        )

    def delete_model(self, request, obj):

        if obj.image:

            delete_old_profile_image(
                obj.image,
                None,
            )

        super().delete_model(
            request,
            obj,
        )

    def delete_queryset(self, request, queryset):

        for obj in queryset:

            if obj.image:

                delete_old_profile_image(
                    obj.image,
                    None,
                )

        super().delete_queryset(
            request,
            queryset,
        )

    @admin.action(description="Activate selected profiles")
    def activate_profiles(self, request, queryset):

        queryset.update(is_active=True)


    @admin.action(description="Deactivate selected profiles")
    def deactivate_profiles(self, request, queryset):

        queryset.update(is_active=False)

    # -------------------------------------------------------------------------
    # SAVE
    # -------------------------------------------------------------------------

    def save_model(
        self,
        request,
        obj,
        form,
        change,
    ):

        if change and "image" in form.changed_data:

            try:

                old = Profile.objects.get(pk=obj.pk)

                delete_old_profile_image(
                    old.image,
                    obj.image,
                )

            except Profile.DoesNotExist:
                pass

        super().save_model(
            request,
            obj,
            form,
            change,
        )




@admin.display(description="Role")
def coloured_role(self, obj):

    colours = {
        "Admin": "#d9534f",
        "HR": "#0275d8",
        "Payroll": "#5bc0de",
        "Accountant": "#5cb85c",
        "Staff": "#6c757d",
        "Supervisor": "#f0ad4e",
        "Client": "#7952b3",
        "Auditor": "#343a40",
    }

    colour = colours.get(obj.user_type, "#777")

    return format_html(
        '<span style="font-weight:bold;color:{};">{}</span>',
        colour,
        obj.user_type,
    )