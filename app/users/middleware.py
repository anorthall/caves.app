from zoneinfo import ZoneInfoNotFoundError

from django.utils import timezone
from users.models import CavingUser, Notification


class DistanceUnitsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            request.units = request.user.units
        else:
            request.units = CavingUser.METRIC

        return self.get_response(request)


class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                tz = request.user.timezone
                timezone.activate(tz)
            except ZoneInfoNotFoundError:  # pragma: no cover
                timezone.deactivate()

        return self.get_response(request)


class LastSeenMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            request.user.last_seen = timezone.now()
            request.user.save(update_fields=["last_seen"])

        return self.get_response(request)


class NotificationsMiddleware:
    """Mark a notification as read if a user goes on the page it links to."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            return self.get_response(request)

        unread_notifications = Notification.objects.filter(
            user=request.user, read=False
        )
        for notification in unread_notifications:
            if notification.get_url() == request.path:
                notification.read = True
                notification.save(updated=False, update_fields=["read"])

        return self.get_response(request)
