from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import CaveEntrance, CaveSystem


class CaveEntranceInline(TabularInline):
    model = CaveEntrance
    fk_name = "system"
    fields = ("name", "region", "country", "coordinates")
    readonly_fields = ("coordinates",)


@admin.register(CaveSystem)
class CaveSystemAdmin(ModelAdmin):
    inlines = [CaveEntranceInline]
    search_fields = (
        "name",
        "user__username",
        "user__name",
        "user__email",
    )
    search_help_text = "Search by system name, or author name, email or username."
    readonly_fields = ("added", "updated", "uuid")
    list_display = (
        "user",
        "name",
        "added",
        "updated",
    )
    list_display_links = ("name",)
    list_filter = ("added", "updated")
    ordering = ("-added",)
    autocomplete_fields = ("user",)
    fieldsets = (
        (
            "Cave system",
            {
                "fields": ("name",),
            },
        ),
        (
            "Internal data",
            {
                "fields": (
                    "user",
                    "uuid",
                    "added",
                    "updated",
                ),
            },
        ),
    )
