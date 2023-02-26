from django.contrib import admin
from .models import Trip

# Set global admin site headers
admin.site.site_header = "Caving Log"
admin.site.site_title = "Caving Log"
admin.site.index_title = "Administration"


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
        "trip_added",
        "trip_updated",
    )
    list_display = (
        "cave_name",
        "user",
        "trip_start",
        "trip_type",
        "trip_added",
    )
    list_filter = (
        "user__username",
        "trip_added",
        "trip_type",
    )
    ordering = (
        "user",
        "-trip_start",
    )
    fieldsets = (
        (
            "Internal data",
            {
                "fields": (
                    "user",
                    "trip_added",
                    "trip_updated",
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
                    "trip_type",
                    "trip_start",
                    "trip_end",
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
