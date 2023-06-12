from django.contrib import admin
from django.forms import ModelForm
from logger.forms import DistanceUnitFormMixin

from .models import Trip, TripPhoto, TripReport


class TripAdminForm(DistanceUnitFormMixin, ModelForm):
    pass


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    form = TripAdminForm
    search_fields = (
        "cave_name",
        "cave_entrance",
        "cave_exit",
        "cave_region",
        "cave_country",
        "cavers",
        "clubs",
        "expedition",
        "notes",
    )
    readonly_fields = (
        "added",
        "updated",
        "uuid",
    )
    list_display = (
        "user",
        "cave_name",
        "cave_country",
        "privacy",
        "added",
        "start",
    )
    list_filter = (
        "type",
        "privacy",
    )
    ordering = ("-added",)
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
class TripPhotoAdmin(admin.ModelAdmin):
    list_display = ("user", "trip", "taken", "added", "taken", "is_valid")
    list_filter = ("is_valid",)
    search_fields = ("user__username",)
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
class TripReportAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "pub_date", "trip", "privacy")
    list_filter = ("user", "pub_date", "privacy")
    search_fields = ("title", "content")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("added", "updated")
