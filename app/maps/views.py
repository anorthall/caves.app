from core.logging import log_trip_action
from core.utils import get_user
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.gis.geos import Point
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.generic import FormView, TemplateView, View
from django_ratelimit.decorators import ratelimit
from logger.models import Trip

from .forms import BulkLocationForm
from .services import get_lat_long_from, get_markers_for_user


class UserMap(LoginRequiredMixin, TemplateView):
    template_name = "maps/map.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["map_markers"] = get_markers_for_user(get_user(self.request))
        context["google_maps_user_map_id"] = settings.GOOGLE_MAPS_USER_MAP_ID
        context["can_add_more_locations"] = (
            get_user(self.request)
            .trips.filter(Q(cave_coordinates__isnull=True) | Q(cave_location=""))
            .exists()
            and context["map_markers"]
        )
        return context


@method_decorator(cache_page(60 * 60 * 24), name="dispatch")
@method_decorator(
    ratelimit(key="user_or_ip", rate="20/m", block=False), name="dispatch"
)
class HTMXGeocoding(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        query = request.POST.get("cave_location")
        if not query or getattr(request, "limited", False):
            return self.render_results(request)

        try:
            lat, lng = get_lat_long_from(query)
            return self.render_results(request, lat, lng)
        except ValueError:
            return self.render_results(request)

    def render_results(self, request, lat=None, lng=None):
        context = {"lat": lat, "lng": lng}
        return render(request, "maps/_htmx_geocoding_results.html", context)


class AddTripLocation(LoginRequiredMixin, FormView):
    form_class = BulkLocationForm
    template_name = "maps/add_trip_locations.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.trip = None

    def dispatch(self, request, *args, **kwargs):
        self.trip = get_object_or_404(Trip, uuid=self.kwargs.get("trip"))
        if self.trip.user != self.request.user:
            raise PermissionDenied

        if self.trip.cave_coordinates:
            messages.info(
                self.request,
                "This trip already has coordinates. "
                "You can edit them on the trip page.",
            )
            return redirect(self.trip.get_absolute_url())

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.trip
        kwargs["trip"] = self.trip
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["trip"] = self.trip
        context["object_owner"] = self.request.user
        context["remaining_trips_without_location"] = (
            get_user(self.request)
            .trips.filter(Q(cave_coordinates__isnull=True) | Q(cave_location=""))
            .count()
        )
        return context

    def form_valid(self, form):
        additional_trips = form.cleaned_data.get("additional_caves", [])
        trips_to_update = [form.trip] + list(additional_trips)

        for trip in trips_to_update:
            latitude = form.cleaned_data.get("latitude")
            longitude = form.cleaned_data.get("longitude")
            trip.cave_coordinates = Point(longitude, latitude)
            trip.cave_location = form.cleaned_data["cave_location"]
            log_trip_action(get_user(self.request), trip, "added a cave location to")
            trip.save()

        if len(trips_to_update) > 1:
            messages.success(
                self.request, f"Location added to {len(trips_to_update)} trips."
            )
        else:
            messages.success(self.request, "Location added to trip.")
        return redirect(reverse("maps:add_location"))


class FindTripToAddLocation(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        selected_trip = (
            get_user(request)
            .trips.filter(Q(cave_coordinates__isnull=True) | Q(cave_location=""))
            .order_by("?")
            .first()
        )

        if not selected_trip:
            messages.success(
                self.request, "All your trips have locations added. Great job!"
            )
            return redirect("maps:index")

        return redirect(reverse("maps:add_location_form", args=[selected_trip.uuid]))
