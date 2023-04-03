from django.contrib import admin
from .models import News, FAQ


# Set global admin site headers
admin.site.site_header = "caves.app"
admin.site.site_title = "caves.app"
admin.site.index_title = "Administration"


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "posted_at", "added", "updated")
    readonly_fields = ("added", "updated")
    ordering = ("-posted_at",)


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "added", "updated")
    readonly_fields = ("added", "updated")
    ordering = ("updated",)
