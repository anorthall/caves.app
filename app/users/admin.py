from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .forms import UserAdminChangeForm, UserCreationForm
from .models import CavingUser, UserProfile, UserSettings


@admin.register(CavingUser)
class CavingUserAdmin(BaseUserAdmin):
    form = UserAdminChangeForm
    add_form = UserCreationForm

    list_display = (
        "email",
        "username",
        "date_joined",
        "last_login",
        "last_seen",
        "is_active",
    )
    list_filter = (
        "is_active",
        "last_login",
        "last_seen",
    )
    fieldsets = (
        (
            "Account details",
            {
                "fields": (
                    "email",
                    "username",
                )
            },
        ),
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


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    readonly_fields = ("user",)


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    readonly_fields = ("user",)
