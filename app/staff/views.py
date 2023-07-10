from django.contrib.auth import get_user_model
from django.views.generic import RedirectView, TemplateView
from logger.models import Trip, TripPhoto, TripReport

from .mixins import StaffRequiredMixin
from .statistics import get_time_statistics

User = get_user_model()


class Dashboard(StaffRequiredMixin, TemplateView):
    template_name = "staff/dashboard.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        trips = Trip.objects.all()
        trip_reports = TripReport.objects.all()
        users = User.objects.all()
        photos_valid = TripPhoto.objects.valid()
        photos_invalid = TripPhoto.objects.invalid()
        photos_deleted = TripPhoto.objects.deleted()

        statistics = [
            get_time_statistics(trips),
            get_time_statistics(trips, metric="Updated", lookup="updated__gte"),
            get_time_statistics(trip_reports),
            get_time_statistics(trip_reports, metric="Updated", lookup="updated__gte"),
            get_time_statistics(photos_valid, metric="Valid", lookup="added__gte"),
            get_time_statistics(photos_invalid, metric="Invalid", lookup="added__gte"),
            get_time_statistics(
                photos_deleted, metric="Deleted", lookup="deleted_at__gte"
            ),
            get_time_statistics(users, metric="New", lookup="date_joined__gte"),
            get_time_statistics(users, metric="Active", lookup="last_seen__gte"),
        ]

        context["statistics"] = statistics
        return context


class Index(StaffRequiredMixin, RedirectView):
    pattern_name = "staff:dashboard"
