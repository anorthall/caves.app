from django.contrib import admin
from .models import Trip


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    search_fields = (
        "cave_name",
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
                    "aid_dist",
                ),
            },
        ),
        ("Notes", {"fields": ("notes",)}),
    )
