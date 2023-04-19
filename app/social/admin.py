from django.contrib import admin

from .models import FriendRequest, Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["user", "message", "read", "added"]
    list_filter = ["user", "read"]
    search_fields = ["user", "message"]
    readonly_fields = ["added"]
    fieldsets = ((None, {"fields": ("user", "message", "url", "read", "added")}),)


@admin.register(FriendRequest)
class FriendRequestAdmin(admin.ModelAdmin):
    list_display = ["user_from", "user_to", "created"]
    list_filter = ["user_from", "user_to"]
    search_fields = ["user_from", "user_to"]
    readonly_fields = ["created"]
    fieldsets = ((None, {"fields": ("user_from", "user_to", "created")}),)
