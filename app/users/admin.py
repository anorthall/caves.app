from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CavingUser
from .forms import UserCreationForm, UserAdminChangeForm


class CavingUserAdmin(BaseUserAdmin):
    form = UserAdminChangeForm
    add_form = UserCreationForm

    list_display = (
        "email",
        "username",
        "name",
        "location",
        "privacy",
        "date_joined",
        "last_login",
        "last_seen",
        "is_active",
    )
    list_filter = (
        "is_active",
        "privacy",
        "last_login",
        "last_seen",
    )
    fieldsets = (
        (
            "Contact details",
            {
                "fields": (
                    "name",
                    "username",
                    "email",
                )
            },
        ),
        (
            "Personal details",
            {
                "fields": (
                    "location",
                    "country",
                    "clubs",
                )
            },
        ),
        (
            "Profile settings",
            {
                "fields": (
                    "privacy",
                    "profile_page_title",
                    "bio",
                    "show_statistics",
                    "private_notes",
                )
            },
        ),
        ("Friends", {"fields": ("friends",)}),
        ("Settings", {"fields": ("units", "timezone")}),
        # ("Permissions", {"fields": ("user_permissions",)}),
        (
            "Authentication",
            {"fields": ("last_login", "last_seen", "is_active", "is_superuser")},
        ),
    )

    readonly_fields = ("last_login", "last_seen")

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "username",
                    "name",
                    "password1",
                    "password2",
                    "is_active",
                ),
            },
        ),
    )

    search_fields = (
        "email",
        "username",
        "bio",
        "clubs",
    )
    ordering = ("-date_joined",)
    filter_horizontal = ()


admin.site.register(CavingUser, CavingUserAdmin)
