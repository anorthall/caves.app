from django.contrib import admin

from .models import FAQ, News

# Set global admin site headers
admin.site.site_header = "caves.app"
admin.site.site_title = "caves.app"
admin.site.index_title = "Administration"


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "posted_at", "added", "updated")
    readonly_fields = ("added", "updated", "author")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "title",
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

    def save_model(self, request, obj, form, change):
        """Set the author to the current user if it is a new news item"""
        if obj.author is None:
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "added", "updated")
    readonly_fields = ("added", "updated")
    ordering = ("updated",)
