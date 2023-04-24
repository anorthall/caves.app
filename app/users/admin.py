from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .forms import UserAdminChangeForm, UserCreationForm
from .models import CavingUser, FriendRequest, Notification, UserProfile, UserSettings


class NotificationInline(admin.TabularInline):
    model = Notification
    readonly_fields = ["message", "url", "read"]
    can_delete = False
    extra = 0
    max_num = 0


class FriendRequestSentInline(admin.TabularInline):
    model = FriendRequest
    readonly_fields = ["user_from"]
    can_delete = False
    fk_name = "user_from"
    verbose_name = "sent friend request"
    extra = 0
    max_num = 0


class FriendRequestRecdInline(admin.TabularInline):
    model = FriendRequest
    readonly_fields = ["user_to"]
    can_delete = False
    fk_name = "user_to"
    verbose_name = "received friend request"
    extra = 0
    max_num = 0


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    autocomplete_fields = ["friends"]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "avatar",
                    "location",
                    "country",
                    "clubs",
                    "page_title",
                    "friends",
                    "bio",
                )
            },
        ),
    )


class UserSettingsInline(admin.StackedInline):
    model = UserSettings
    can_delete = False
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "privacy",
                    "units",
                    "timezone",
                    "private_notes",
                    "show_statistics",
                )
            },
        ),
    )


@admin.register(CavingUser)
class CavingUserAdmin(BaseUserAdmin):
    form = UserAdminChangeForm
    add_form = UserCreationForm

    list_display = (
        "email",
        "username",
        "name",
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
                    "name",
                    "last_login",
                    "last_seen",
                    "is_active",
                    "is_superuser",
                )
            },
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
        "name",
    )
    ordering = ("-date_joined",)
    filter_horizontal = ()
    inlines = [
        UserProfileInline,
        UserSettingsInline,
        NotificationInline,
        FriendRequestSentInline,
        FriendRequestRecdInline,
    ]
