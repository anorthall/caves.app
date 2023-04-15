from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["user", "message", "read", "added"]
    list_filter = ["user", "read"]
    search_fields = ["user", "message"]
    readonly_fields = ["added"]
    fieldsets = ((None, {"fields": ("user", "message", "url", "read", "added")}),)
