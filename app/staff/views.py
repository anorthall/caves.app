from comments.models import Comment
from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from django.views.generic import RedirectView, TemplateView
from logger.models import Caver, Trip, TripPhoto

from .mixins import ModeratorRequiredMixin
from .statistics import get_integer_field_statistics, get_time_statistics

User = get_user_model()


class Dashboard(ModeratorRequiredMixin, TemplateView):
    template_name = "staff/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        trips = Trip.objects.all()
        users = User.objects.all()
        comments = Comment.objects.all()
        cavers = Caver.objects.all()
        photos = TripPhoto.objects.filter(is_valid=True)
        photos_valid = TripPhoto.objects.valid()
        photos_deleted = TripPhoto.objects.deleted()

        statistics = [
            get_time_statistics(photos_valid, metric="Valid", lookup="added__gte"),
            get_time_statistics(
                photos_deleted, metric="Deleted", lookup="deleted_at__gte"
            ),
            get_integer_field_statistics(photos, "Total storage", "filesize"),
            get_integer_field_statistics(
                photos_deleted, "Deleted storage", "filesize", "deleted_at__gte"
            ),
            get_time_statistics(cavers),
            get_time_statistics(comments),
            get_time_statistics(trips),
            get_time_statistics(users, metric="New", lookup="date_joined__gte"),
            get_time_statistics(users, metric="Active", lookup="last_seen__gte"),
        ]

        context["statistics"] = statistics

        context["recent_trips"] = (
            Trip.objects.all()
            .order_by("-added")
            .select_related("user")
            .prefetch_related("comments", "photos", "user__friends")
            .annotate(
                comment_count=Count("comments", distinct=True),
                photo_count=Count("photos", distinct=True),
                like_count=Count("likes", distinct=True),
            )[:30]
        )

        for trip in context["recent_trips"]:
            if not trip.is_viewable_by(self.request.user):
                trip.cave_name = "Private trip"

            if not trip.user.is_viewable_by(self.request.user):
                trip.user.name = "Private user"

        context["active_users"] = (
            User.objects.filter(is_active=True)
            .order_by("-last_seen")
            .annotate(
                trip_count=Count("trip", distinct=True),
                trip_views=Sum("trip__view_count", distinct=True, default=0),
            )[:30]
        )

        for user in context["active_users"]:
            if not user.is_viewable_by(self.request.user):
                user.name = "Private user"

        return context


class Index(ModeratorRequiredMixin, RedirectView):
    pattern_name = "staff:dashboard"
