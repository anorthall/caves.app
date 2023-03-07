from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CavingUser
from .forms import UserCreationForm, UserAdminChangeForm


class CavingUserAdmin(BaseUserAdmin):
    form = UserAdminChangeForm
    add_form = UserCreationForm

    list_display = ("email", "username", "first_name", "last_name", "location")
    list_filter = ()
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
                    "club",
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
                ),
            },
        ),
    )

    search_fields = ("email",)
    ordering = ("email",)
    filter_horizontal = ()


admin.site.register(CavingUser, CavingUserAdmin)
