from django.contrib import admin
from .models import Trip, Cave


@admin.register(Cave)
class CaveAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "region",
        "country",
        "added_by",
    )
    search_fields = (
        "name",
        "region",
        "country",
        "added_by",
    )
    list_filter = (
        "added_by__username",
        "country",
        "region",
    )
    readonly_fields = ("added",)
    fieldsets = (
        (
            "Cave details",
            {
                "fields": (
                    "name",
                    "region",
                    "country",
                )
            },
        ),
        (
            "Internal data",
            {
                "fields": (
                    "added",
                    "added_by",
                )
            },
        ),
    )
    ordering = (
        "added_by",
        "country",
        "name",
    )


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    search_fields = (
        "cave_name",
        "cave_region",
        "cave_country",
        "cavers",
        "club",
        "expedition",
        "notes",
    )
    readonly_fields = (
        "added",
        "updated",
    )
    list_display = (
        "cave_name",
        "user",
        "start",
        "type",
        "added",
    )
    list_filter = (
        "user__username",
        "added",
        "type",
    )
    ordering = (
        "user",
        "-start",
    )
    fieldsets = (
        (
            "Internal data",
            {
                "fields": (
                    "user",
                    "privacy",
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
                    "club",
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
                    "aid_dist",
                ),
            },
        ),
        ("Notes", {"fields": ("notes",)}),
    )
