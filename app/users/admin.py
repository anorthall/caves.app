from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.admin import ModelAdmin, TabularInline

from .forms import UserAdminChangeForm, UserCreationForm
from .models import FriendRequest

User = get_user_model()


class FriendRequestSentInline(TabularInline):
    model = FriendRequest
    readonly_fields = ["user_from"]
    can_delete = False
    fk_name = "user_from"
    verbose_name = "sent friend request"
    extra = 0
    max_num = 0


class FriendRequestRecdInline(TabularInline):
    model = FriendRequest
    readonly_fields = ["user_to"]
    can_delete = False
    fk_name = "user_to"
    verbose_name = "received friend request"
    extra = 0
    max_num = 0


@admin.register(User)
class CavingUserAdmin(BaseUserAdmin, ModelAdmin):
    inlines = [
        FriendRequestSentInline,
        FriendRequestRecdInline,
    ]
    readonly_fields = (
        "last_login",
        "last_seen",
        "date_joined",
        "uuid",
        "friends",
        "has_verified_email",
    )
    form = UserAdminChangeForm
    add_form = UserCreationForm
    search_fields = (
        "email",
        "username",
        "name",
        "bio",
    )
    search_help_text = "Search by email, username, name or bio."
    ordering = ("-last_seen",)
    autocomplete_fields = ["friends"]
    list_display = (
        "email",
        "username",
        "date_joined",
        "last_seen",
    )
    list_filter = (
        "is_active",
        "has_verified_email",
        "is_superuser",
        "last_seen",
    )
    fieldsets = (
        (
            "Account details",
            {
                "fields": (
                    "email",
                    "username",
                    "name",
                    "uuid",
                    "last_login",
                    "last_seen",
                    "date_joined",
                    "is_active",
                    "has_mod_perms",
                    "is_superuser",
                    "has_verified_email",
                )
            },
        ),
        (
            "Profile",
            {
                "fields": (
                    "location",
                    "country",
                    "clubs",
                ),
            },
        ),
        (
            "Social",
            {
                "fields": (
                    "bio",
                    "friends",
                ),
            },
        ),
        (
            "Settings",
            {
                "fields": (
                    "timezone",
                    "units",
                    "privacy",
                    "allow_friend_email",
                    "allow_friend_username",
                    "allow_comments",
                    "email_friend_requests",
                ),
            },
        ),
        (
            "Custom fields",
            {
                "fields": (
                    "custom_field_1_label",
                    "custom_field_2_label",
                    "custom_field_3_label",
                    "custom_field_4_label",
                    "custom_field_5_label",
                )
            },
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
                    "name",
                    "password1",
                    "password2",
                    "is_active",
                ),
            },
        ),
    )
