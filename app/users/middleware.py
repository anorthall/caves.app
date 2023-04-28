from zoneinfo import ZoneInfoNotFoundError

from django.utils import timezone


class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """
        Get and set the user timezone from their profile.
        This could be later improved by caching the timezone in the session.
        """
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
