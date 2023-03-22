from django import forms
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
        "first_name",
        "last_name",
        "location",
        "date_joined",
        "is_active",
    )
    list_filter = ("is_active",)
    fieldsets = (
        (
            "Contact details",
            {
                "fields": (
                    "first_name",
                    "last_name",
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
                    "bio",
                )
            },
        ),
        ("Settings", {"fields": ("units", "timezone")}),
        ("Permissions", {"fields": ("user_permissions",)}),
        (
            "Authentication",
            {"fields": ("is_active", "is_superuser", "password")},
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "username",
                    "first_name",
                    "last_name",
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
