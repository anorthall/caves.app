from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.views.generic import ListView
from stats import statistics as new_stats
from users.models import CavingUser as User

from ..models import Trip


class UserProfile(ListView):
    """List all of a user's trips and their profile information"""

    model = Trip
    template_name = "logger/profile.html"
    context_object_name = "trips"
    slug_field = "username"
    paginate_by = 50
    ordering = ("-start", "pk")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.profile_user = None

    def setup(self, *args, **kwargs):
        """Assign self.profile_user and perform permissions checks"""
        super().setup(*args, **kwargs)
        self.profile_user = get_object_or_404(User, username=self.kwargs["username"])
        if not self.profile_user.is_viewable_by(self.request.user):
            raise PermissionDenied

    def get_queryset(self):
        trips = (
            Trip.objects.filter(user=self.profile_user)
            .select_related("report")
            .order_by(*self.get_ordering())
        )

        # Sanitise trips to be privacy aware
        if not self.profile_user == self.request.user:
            sanitised_trips = [x for x in trips if x.is_viewable_by(self.request.user)]
            return sanitised_trips
        else:
            return trips

    def get_ordering(self):
        allowed_ordering = [
            "start",
            "cave_name",
            "duration",
            "type",
            "vert_dist_up",
            "vert_dist_down",
        ]

        ordering = self.request.GET.get("sort", "")
        if ordering.replace("-", "") in allowed_ordering:
            return ordering, "pk"

        return self.ordering

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["profile_user"] = self.profile_user
        context["page_title"] = self.get_page_title()
        context["show_cavers"] = self.profile_user.show_cavers_on_trip_list
        if self.profile_user.public_statistics:
            context["stats"] = new_stats.yearly(self.get_queryset())

        # This code provides the current GET parameters as a context variable
        # so that when a pagination link is clicked, the GET parameters are
        # preserved (for sorting).
        parameters = self.request.GET.copy()
        parameters = parameters.pop("page", True) and parameters.urlencode()
        context["get_parameters"] = parameters

        return context

    def get_page_title(self):
        if self.profile_user.page_title:
            return self.profile_user.page_title
        else:
            return f"{self.profile_user.name}'s trips"
