from django.conf import settings
from django.utils import timezone
from zoneinfo import ZoneInfoNotFoundError


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
            except ZoneInfoNotFoundError:
                timezone.deactivate()

        return self.get_response(request)
