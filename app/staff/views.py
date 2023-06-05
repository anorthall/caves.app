from django.contrib.auth import get_user_model
from django.views.generic import RedirectView, TemplateView
from logger.models import Trip, TripReport

from .mixins import StaffRequiredMixin
from .statistics import get_time_statistics

User = get_user_model()


class Dashboard(StaffRequiredMixin, TemplateView):
    template_name = "staff/dashboard.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        statistics = [
            get_time_statistics(Trip),
            get_time_statistics(Trip, metric="Updated", lookup="updated__gte"),
            get_time_statistics(TripReport),
            get_time_statistics(TripReport, metric="Updated", lookup="updated__gte"),
            get_time_statistics(User, metric="New", lookup="date_joined__gte"),
            get_time_statistics(User, metric="Active", lookup="last_seen__gte"),
        ]
        context["statistics"] = statistics
        return context


class Index(StaffRequiredMixin, RedirectView):
    pattern_name = "staff:dashboard"
