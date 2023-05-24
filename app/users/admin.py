from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .forms import UserAdminChangeForm, UserCreationForm
from .models import FriendRequest, Notification

User = get_user_model()


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


@admin.register(User)
class CavingUserAdmin(BaseUserAdmin):
    form = UserAdminChangeForm
    add_form = UserCreationForm

    autocomplete_fields = ["friends"]
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
                    "date_joined",
                    "is_active",
                    "is_superuser",
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
                    "page_title",
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
                    "public_statistics",
                    "private_notes",
                ),
            },
        ),
    )

    readonly_fields = ("last_login", "last_seen", "date_joined")

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
        "bio",
    )
    ordering = ("-last_seen",)
    filter_horizontal = ()
    inlines = [
        NotificationInline,
        FriendRequestSentInline,
        FriendRequestRecdInline,
    ]
