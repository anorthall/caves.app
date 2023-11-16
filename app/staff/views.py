from comments.models import Comment
from django.contrib.auth import get_user_model
from django.views.generic import RedirectView, TemplateView
from logger.models import Caver, Trip, TripPhoto

from .mixins import ModeratorRequiredMixin
from .statistics import get_integer_field_statistics, get_time_statistics

User = get_user_model()


class Dashboard(ModeratorRequiredMixin, TemplateView):
    template_name = "staff/dashboard.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        trips = Trip.objects.all()
        users = User.objects.all()
        comments = Comment.objects.all()
        cavers = Caver.objects.all()
        photos = TripPhoto.objects.filter(is_valid=True)
        photos_valid = TripPhoto.objects.valid()
        photos_deleted = TripPhoto.objects.deleted()

        statistics = [
            get_time_statistics(trips),
            get_time_statistics(trips, metric="Updated", lookup="updated__gte"),
            get_time_statistics(cavers),
            get_time_statistics(cavers, metric="Updated", lookup="updated__gte"),
            get_time_statistics(comments),
            get_time_statistics(photos_valid, metric="Valid", lookup="added__gte"),
            get_time_statistics(
                photos_deleted, metric="Deleted", lookup="deleted_at__gte"
            ),
            get_integer_field_statistics(photos, "Total storage", "filesize"),
            get_integer_field_statistics(
                photos_deleted, "Deleted storage", "filesize", "deleted_at__gte"
            ),
            get_time_statistics(users, metric="New", lookup="date_joined__gte"),
            get_time_statistics(users, metric="Active", lookup="last_seen__gte"),
        ]

        context["statistics"] = statistics
        return context


class Index(ModeratorRequiredMixin, RedirectView):
    pattern_name = "staff:dashboard"
