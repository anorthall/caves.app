from distancefield import DistanceField
from django.contrib import admin
from django.forms import ModelForm
from logger.forms import DistanceUnitFormMixin
from unfold.admin import ModelAdmin, TabularInline
from unfold.widgets import UnfoldAdminTextInputWidget

from .models import Trip, TripPhoto, TripReport


class TripAdminForm(DistanceUnitFormMixin, ModelForm):
    pass


class TripPhotoInline(TabularInline):
    model = TripPhoto
    fk_name = "trip"
    extra = 0
    max_num = 0
    show_change_link = True
    fields = ("photo", "caption", "is_valid", "deleted_at", "taken")

    def has_add_permission(self, request, obj=None):
        return False


class TripReportInline(TabularInline):
    model = TripReport
    fk_name = "trip"
    extra = 0
    max_num = 0
    show_change_link = True
    fields = ("title", "pub_date")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Trip)
class TripAdmin(ModelAdmin):
    form = TripAdminForm
    inlines = [TripPhotoInline, TripReportInline]
    search_fields = (
        "cave_name",
        "cave_entrance",
        "cave_exit",
        "cave_region",
        "cave_country",
        "user__username",
        "user__name",
        "user__email",
    )
    search_help_text = (
        "Search by cave name, region and country, or author name, email or username."
    )
    readonly_fields = (
        "added",
        "updated",
        "uuid",
    )
    list_display = (
        "user",
        "cave_name",
        "start",
        "added",
    )
    list_display_links = ("cave_name",)
    list_filter = (
        "type",
        "added",
        "updated",
    )
    ordering = ("-added",)
    formfield_overrides = {
        DistanceField: {
            "widget": UnfoldAdminTextInputWidget,
        }
    }
    fieldsets = (
        (
            "Internal data",
            {
                "fields": (
                    "user",
                    "privacy",
                    "uuid",
                    "added",
                    "updated",
                ),
            },
        ),
        (
            "Cave details",
            {
                "fields": (
                    "cave_name",
                    "cave_entrance",
                    "cave_exit",
                    "cave_region",
                    "cave_country",
                ),
            },
        ),
        (
            "Trip details",
            {
                "fields": (
                    "type",
                    "start",
                    "end",
                ),
            },
        ),
        (
            "Attendees",
            {
                "fields": (
                    "cavers",
                    "clubs",
                    "expedition",
                ),
            },
        ),
        (
            "Distances",
            {
                "fields": (
                    "horizontal_dist",
                    "vert_dist_down",
                    "vert_dist_up",
                    "surveyed_dist",
                    "resurveyed_dist",
                    "aid_dist",
                ),
            },
        ),
        ("Notes", {"fields": ("notes",)}),
    )


@admin.register(TripPhoto)
class TripPhotoAdmin(ModelAdmin):
    list_display = ("user", "trip", "deleted_at", "taken", "added")
    list_display_links = ("taken",)
    list_filter = ("is_valid", "deleted_at", "added")
    search_fields = ("user__username", "user__name", "user__email", "trip__uuid")
    search_help_text = "Search by author name, email or username, or trip UUID."
    autocomplete_fields = ("trip", "user")
    readonly_fields = ("added", "updated", "uuid", "taken")
    ordering = ("-added",)
    fieldsets = (
        (
            "Internal data",
            {
                "fields": (
                    "user",
                    "trip",
                    "is_valid",
                    "deleted_at",
                    "uuid",
                    "taken",
                    "added",
                    "updated",
                ),
            },
        ),
        (
            "Photo details",
            {
                "fields": (
                    "caption",
                    "photo",
                ),
            },
        ),
    )


@admin.register(TripReport)
class TripReportAdmin(ModelAdmin):
    list_display = ("user", "title", "trip", "added")
    list_display_links = ("title",)
    list_filter = ("added", "updated", "pub_date")
    ordering = ("-added",)
    search_fields = (
        "title",
        "user__username",
        "user__name",
        "user__email",
        "trip__uuid",
    )
    search_help_text = (
        "Search by title or trip UUID, or by author name, email or username."
    )
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("added", "updated")
