from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CavingUser
from .forms import UserCreationForm, UserChangeForm


class CavingUserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ("email", "username", "first_name", "last_name", "location")
    list_filter = ()
    fieldsets = (
        (
            "Personal info",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "username",
                    "email",
                    "location",
                    "bio",
                )
            },
        ),
        ("Settings", {"fields": ("units", "timezone")}),
        ("Authentication", {"fields": ("user_permissions", "password")}),
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
