from typing import Union

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import ListView, TemplateView
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
        self.profile_user: Union[User, None] = None

    def setup(self, *args, **kwargs):
        """Assign self.profile_user and perform permissions checks"""
        super().setup(*args, **kwargs)
        self.profile_user = get_object_or_404(User, username=self.kwargs["username"])
        self.profile_user.add_profile_view(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["profile_user"] = self.profile_user
        context["mutual_friends"] = self.profile_user.mutual_friends(self.request.user)
        context["user_has_trips"] = self.profile_user.trips.exists()
        context["photos"] = self.profile_user.get_photos(for_user=self.request.user)
        context["quick_stats"] = self.profile_user.quick_stats
        context["show_stats_link"] = self.profile_user == self.request.user

        if self.request.user not in self.profile_user.friends.all():
            if self.profile_user.allow_friend_username:
                context["can_add_friend"] = True

        if not self.profile_user.is_viewable_by(self.request.user):
            context["private_profile"] = True

        if self.profile_user.public_statistics:
            context["stats"] = statistics.yearly(
                self.profile_user.trips.exclude(type=Trip.SURFACE)
            )

        return context


class ProfileTripsTable(ListView):
    """List all of a user's trips and their profile information"""

    model = Trip
    template_name = "logger/profile_trips_table.html"
    context_object_name = "trips"
    slug_field = "username"
    paginate_by = 100
    ordering = ("-start", "pk")
    allowed_ordering = [
        "start",
        "cave_name",
        "duration",
        "type",
        "vert_dist_up",
        "vert_dist_down",
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.profile_user = None
        self.allow_sort = True
        self.query = None

    def setup(self, *args, **kwargs):
        """Assign self.profile_user and perform permissions checks"""
        super().setup(*args, **kwargs)
        self.profile_user = get_object_or_404(User, username=self.kwargs["username"])

    def get_queryset(self):
        query = self.request.GET.get("query", "")
        if len(query) < 3:
            query = None
        self.query = query

        trips = (
            Trip.objects.filter(user=self.profile_user)
            .select_related("user")
            .prefetch_related("photos", "cavers")
        )

        if query:
            distinct_query = self.get_ordering()
            distinct_query = [x.replace("-", "") for x in distinct_query]

            trips = (
                trips.filter(
                    Q(cave_name__unaccent__icontains=query)
                    | Q(cave_entrance__unaccent__icontains=query)
                    | Q(cave_exit__unaccent__icontains=query)
                    | Q(cavers__name__unaccent__icontains=query)
                    | Q(clubs__unaccent__icontains=query)
                    | Q(expedition__unaccent__icontains=query)
                )
                .distinct(*distinct_query)
                .order_by(*self.get_ordering())
            )
            self.allow_sort = False
        else:
            trips = trips.order_by(*self.get_ordering())

        friends = self.profile_user.friends.all()

        # Sanitise trips to be privacy aware
        if not self.profile_user == self.request.user:
            sanitised_trips = [
                x for x in trips if x.is_viewable_by(self.request.user, friends)
            ]
            return sanitised_trips
        else:
            return trips

    def get_ordering(self):
        ordering = self.request.GET.get("sort", "").lower()
        if ordering.replace("-", "") in self.allowed_ordering:
            return ordering, "pk"

        return self.ordering

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["profile_user"] = self.profile_user
        context["show_cavers"] = self.profile_user.show_cavers_on_trip_list
        context["htmx_url"] = reverse(
            "log:profile_trips_table", args=[self.profile_user.username]
        )
        context["ordering"] = self.get_ordering()[0]
        context["allow_sort"] = self.allow_sort
        context["query"] = self.query

        # This code provides the current GET parameters as a context variable
        # so that when a pagination link is clicked, the GET parameters are
        # preserved (for sorting).
        parameters = self.request.GET.copy()
        parameters = parameters.pop("page", True) and parameters.urlencode()
        context["get_parameters"] = parameters

        return context
