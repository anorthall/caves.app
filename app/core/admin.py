from django.conf import settings
from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import FAQ, News

# Set global admin site headers
admin.site.site_header = "caves.app"
admin.site.site_title = "caves.app"
admin.site.index_title = "Administration"
if settings.DEBUG:  # pragma: no cover
    admin.site.site_header = "caves.app dev"
    admin.site.site_title = "caves.app dev"


class AutoAssignAuthorModelAdmin(ModelAdmin):
    def save_model(self, request, obj, form, change):
        """Set the author to the current user if it is a new item"""
        if obj.author is None:
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(News)
class NewsAdmin(AutoAssignAuthorModelAdmin):
    list_display = ("title", "author", "posted_at", "added", "updated")
    readonly_fields = ("added", "updated", "author")
    prepopulated_fields = {"slug": ("title",)}
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "title",
                    "slug",
                    "content",
                    "posted_at",
                    "is_published",
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "author",
                    "added",
                    "updated",
                )
            },
        ),
    )
    ordering = ("-posted_at",)


@admin.register(FAQ)
class FAQAdmin(AutoAssignAuthorModelAdmin):
    list_display = ("question", "added", "updated")
    readonly_fields = ("added", "updated", "author")
    ordering = ("updated",)
