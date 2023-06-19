from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.views import View
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

    def setup(self, *args, **kwargs):
        """Assign self.profile_user and perform permissions checks"""
        super().setup(*args, **kwargs)
        self.profile_user = get_object_or_404(User, username=self.kwargs["username"])
        if not self.profile_user.is_viewable_by(self.request.user):
            raise PermissionDenied

    def get_queryset(self):
        trips = (
            Trip.objects.filter(user=self.profile_user)
            .select_related("report", "user")
            .order_by(*self.get_ordering())
        )

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
        ordering = self.request.GET.get("sort", "")
        if ordering.replace("-", "") in self.allowed_ordering:
            return ordering, "pk"

        return self.ordering

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["profile_user"] = self.profile_user
        context["page_title"] = self.get_page_title()
        context["mutual_friends"] = self.profile_user.mutual_friends(self.request.user)
        context["show_cavers"] = self.profile_user.show_cavers_on_trip_list
        if self.profile_user.public_statistics:
            context["stats"] = new_stats.yearly(self.object_list)

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


class HTMXTripListSearchView(View):
    def __init__(self):
        super().__init__()
        self.profile_user = None

    def setup(self, *args, **kwargs):
        """Assign self.profile_user and perform permissions checks"""
        super().setup(*args, **kwargs)
        self.profile_user = get_object_or_404(User, username=self.kwargs["username"])
        if not self.profile_user.is_viewable_by(self.request.user):
            raise PermissionDenied

    def post(self, request, *args, **kwargs):
        """Return a list of trips matching the search query"""
        query = request.POST.get("query", "")
        if len(query) < 3:
            return render(
                request,
                "logger/_htmx_trip_list_search.html",
                {"trips": None, "query": query},
            )

        trips = Trip.objects.filter(
            Q(user=self.profile_user)
            & Q(
                Q(cave_name__unaccent__icontains=query)
                | Q(cave_entrance__unaccent__icontains=query)
                | Q(cave_exit__unaccent__icontains=query)
                | Q(cavers__unaccent__icontains=query)
                | Q(clubs__unaccent__icontains=query)
                | Q(expedition__unaccent__icontains=query)
            )
        ).order_by("-start", "pk")[:10]

        friends = self.profile_user.friends.all()

        # Sanitise trips to be privacy aware
        if not self.profile_user == self.request.user:
            sanitised_trips = [
                x for x in trips if x.is_viewable_by(self.request.user, friends)
            ]
            trips = sanitised_trips

        return render(
            request,
            "logger/_htmx_trip_list_search.html",
            {"trips": trips, "query": query},
        )
