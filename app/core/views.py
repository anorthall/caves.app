import humanize
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.views.generic import TemplateView
from logger.models import Trip

from .mixins import AuthStateTemplateMixin
from .models import FAQ

User = get_user_model()


class About(AuthStateTemplateMixin, TemplateView):
    template_name = "about/about"

    def get_context_data(self, **kwargs):
        context = {
            "trip_count": Trip.objects.all().count(),
            "user_count": User.objects.all().count(),
            "total_duration": self._get_duration_of_all_trips(),
            "registered": self.request.user.is_authenticated,
        }

        return context

    def _get_duration_of_all_trips(self):
        total_duration = timezone.timedelta(0)
        for trip in Trip.objects.all():
            if trip.duration:
                total_duration += trip.duration

        total_duration_str = humanize.precisedelta(
            total_duration, minimum_unit="hours", format="%.0f"
        )

        return total_duration_str


class Help(AuthStateTemplateMixin, TemplateView):
    template_name = "help/help"

    def get_context_data(self, **kwargs):
        context = {"faqs": FAQ.objects.all().order_by("updated")}
        return context
