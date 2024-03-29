from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Comment


@admin.register(Comment)
class CommentAdmin(ModelAdmin):
    list_display = ("author", "trip", "added")
    list_filter = ("added",)
    search_fields = ("content", "trip__uuid", "author__username", "author__email")
    readonly_fields = ("added", "updated", "trip", "author")
    ordering = ("-added",)
    fieldsets = (
        (
            "Comment",
            {
                "fields": (
                    "author",
                    "trip",
                    "content",
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "added",
                    "updated",
                )
            },
        ),
    )
