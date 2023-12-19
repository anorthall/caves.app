from typing import Optional

from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django_ratelimit.decorators import ratelimit
from stats import statistics
from users.models import CavingUser as User

from ..models import Trip


@method_decorator(ratelimit(key="user_or_ip", rate="500/h"), name="dispatch")
class UserProfile(TemplateView):
    """List all of a user's trips and their profile information"""

    model = Trip
    template_name = "logger/profile.html"
    slug_field = "username"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.profile_user: Optional[User] = None

    def setup(self, *args, **kwargs):
        super().setup(*args, **kwargs)
        self.profile_user = get_object_or_404(User, username=self.kwargs["username"])

    def get(self, request, *args, **kwargs):
        self.profile_user.add_profile_view(self.request)
        return super().get(request, *args, **kwargs)

    def get_trips(self, for_user: User) -> list[Trip]:
        trips = (
            Trip.objects.filter(user=self.profile_user)
            .select_related("user")
            .prefetch_related("photos", "cavers")
            .order_by("-start")
        )

        for trip in trips:
            trip.total_surveyed_dist = trip.surveyed_dist + trip.resurveyed_dist

        # Remove trips that the user cannot view
        if (self.profile_user == for_user) or for_user.is_superuser:
            return trips
        else:
            friends = self.profile_user.friends.all()
            return [x for x in trips if x.is_viewable_by(for_user, friends)]

    # noinspection PyTypeChecker
    def get_context_data(self, **kwargs):
        user: User = self.request.user
        context = super().get_context_data()
        context["profile_user"] = self.profile_user
        context["mutual_friends"] = self.profile_user.mutual_friends(user)

        if user not in self.profile_user.friends.all():
            if self.profile_user.allow_friend_username:
                context["can_add_friend"] = True

        if user.is_superuser or self.profile_user.is_viewable_by(user):
            if user.is_superuser and not self.profile_user.is_viewable_by(user):
                messages.warning(self.request, "Viewing profile in administrator mode.")

            context["trips"] = self.get_trips(user)
            context["photos"] = self.profile_user.get_photos(for_user=user)
            context["quick_stats"] = self.profile_user.quick_stats
            context["stats"] = statistics.yearly(
                self.profile_user.trips.exclude(type=Trip.SURFACE)
            )
            context["enable_private_stats"] = (
                self.profile_user == user
            ) or user.is_superuser
        else:
            context["private_profile"] = True

        return context
