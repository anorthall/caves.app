from core.logging import log_trip_action
from core.utils import get_user
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Exists, OuterRef
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import TemplateView
from django_ratelimit.decorators import ratelimit
from users.models import CavingUser as User
from users.models import Notification

from .. import services
from ..models import Trip


class Index(TemplateView):
    @method_decorator(ratelimit(key="user_or_ip", rate="500/h", group="feed"))
    def get(self, request, *args, **kwargs):
        """Determine if the user is logged in and render the appropriate template."""
        if request.user.is_authenticated:
            context = self.get_authenticated_context(**kwargs)
            return self.render_to_response(context)
        self.template_name = "core/index_unregistered.html"
        return super().get(request, *args, **kwargs)

    def get_authenticated_context(self, **kwargs):
        """Return the trip feed for a logged in user."""
        context = super().get_context_data(**kwargs)
        user = get_user(self.request)
        context["ordering"] = user.feed_ordering
        context["trips"] = services.get_trips_context(self.request, context["ordering"])
        context["quick_stats"] = user.quick_stats
        context["liked_str"] = services.get_liked_str_context(self.request, context["trips"])

        # If there are no trips, show the new user page
        if context["trips"]:
            self.template_name = "logger/social_feed.html"
            services.bulk_update_view_count(self.request, context["trips"])
        else:
            self.template_name = "core/new_user.html"

        return context


class SetFeedOrdering(LoginRequiredMixin, View):
    @method_decorator(ratelimit(key="user", rate="30/h"))
    def post(self, request, *args, **kwargs):
        """Get the ordering from GET params and save it to the user model if it is valid."""
        allowed_ordering = [User.FEED_ADDED, User.FEED_DATE]
        if self.request.POST.get("sort") in allowed_ordering:
            self.request.user.feed_ordering = self.request.POST.get("sort")
            self.request.user.save()
        return redirect(reverse("log:index"))


class HTMXTripLike(LoginRequiredMixin, TemplateView):
    """HTMX view for toggling a trip like."""

    template_name = "logger/_htmx_trip_like.html"

    @method_decorator(ratelimit(key="user", rate="100/h"))
    def post(self, request, uuid):
        trip = self._get_trip(request, uuid)

        if trip.user_liked:  # User already liked, so remove the existing like
            trip.likes.remove(request.user)
            trip.user_liked = False
            log_trip_action(request.user, trip, "unliked")

            if not trip.likes.exists():
                # Delete the notification if there are no likes left
                notification = self._get_trip_like_notification(trip)
                if notification:
                    notification.delete()

        else:  # A new like, so add it
            trip.likes.add(request.user)
            trip.user_liked = True
            log_trip_action(request.user, trip, "liked")

            # Create a notification for the trip owner if one doesn't already exist
            if request.user != trip.user:
                notification = self._get_trip_like_notification(trip)
                if notification:
                    notification.read = False
                    notification.save()
                else:
                    Notification.objects.create(
                        trip=trip, user=trip.user, type=Notification.TRIP_LIKE
                    )

        friends = request.user.friends.all()
        liked_str = {trip.pk: trip.get_liked_str(request.user, friends)}

        context = {
            "trip": trip,
            "liked_str": liked_str,
            "likes_count": trip.likes.count(),
        }

        return self.render_to_response(context)

    def _get_trip(self, request, uuid):
        trip = (
            Trip.objects.filter(uuid=uuid)
            .annotate(
                user_liked=Exists(
                    User.objects.filter(pk=request.user.pk, liked_trips=OuterRef("pk")).only("pk")
                )
            )
            .first()
        )

        if not trip:
            raise Http404

        if trip.is_viewable_by(request.user):
            return trip

        raise PermissionDenied

    def _get_trip_like_notification(self, trip) -> Notification | None:
        """Get the notification for the trip like, if it exists."""
        try:
            return Notification.objects.get(trip=trip, user=trip.user, type=Notification.TRIP_LIKE)
        except Notification.DoesNotExist:
            pass
        return None


@method_decorator(ratelimit(key="user", rate="500/h", group="feed"), name="dispatch")
class HTMXTripFeed(LoginRequiredMixin, TemplateView):
    """Render more trips to be inserted into the trip feed via HTMX."""

    template_name = "logger/_feed.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ordering"] = get_user(self.request).feed_ordering
        context["trips"] = services.get_trips_context(
            request=self.request,
            ordering=context["ordering"],
            page=self.request.GET.get("page", 1),
        )
        context["liked_str"] = services.get_liked_str_context(self.request, context["trips"])

        services.bulk_update_view_count(self.request, context["trips"])

        return context
