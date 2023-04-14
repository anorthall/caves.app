import csv, humanize
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.utils.timezone import localtime as lt
from django.http import HttpResponse, Http404
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import (
    UpdateView,
    DetailView,
    CreateView,
    DeleteView,
    ListView,
)

from .templatetags.distformat import distformat
from .models import Trip, TripReport
from .forms import TripForm, TripReportForm
from logger import services, statistics
from core.models import News


def index(request):
    """
    Index page for the entire website

    Unregistered users will be shown a static welcome page

    Registered users will be shown an interface to add/manage
    recent caving trips.
    """
    if not request.user.is_authenticated:
        return render(request, "index_unregistered.html")

    # Get most recent trips
    qs = request.user.trips
    recent_trips = qs.order_by("-start", "pk")[:6]
    trip_count = qs.count()
    recent_trip_count = recent_trips.count()

    # Only display 3 or 6 trips
    if recent_trip_count < 3:
        # Display welcome text until the user has created three trips
        recent_trips = None
    elif recent_trip_count == 4 or recent_trip_count == 5:
        recent_trips = recent_trips[:3]  # Display only three trips

    # Distance stats
    trip_stats = statistics.stats_for_user(qs)
    trip_stats_year = statistics.stats_for_user(qs, year=timezone.now().year)

    context = {
        "recent_trips": recent_trips,
        "trip_count": trip_count,
        "trip_stats": trip_stats,
        "trip_stats_year": trip_stats_year,
        "dist_format": request.user.units,
        "news": News.objects.filter(
            is_published=True, posted_at__lte=timezone.now()
        ).order_by("-posted_at")[:3],
    }
    return render(request, "index_registered.html", context)


@login_required
def export(request):
    """Export a user's trips to CSV file"""
    if not request.POST:  # Display information page
        return render(request, "export.html")

    # Generate HTTP response and the CSV file
    qs = Trip.objects.filter(user=request.user).order_by("start", "pk")
    if not qs:
        messages.error(request, "You do not have any trips to export.")
        return redirect("log:export")

    timestamp = timezone.now().strftime("%Y-%m-%d-%H%M")
    filename = f"{request.user.username}-trips-{timestamp}.csv"
    response = HttpResponse(
        content_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

    writer = csv.writer(response)

    # Headers
    tz = timezone.get_current_timezone()
    writer.writerow(
        [
            "Number",
            "Cave name",
            "Cave region",
            "Cave country",
            "Cave URL",
            f"Trip start ({tz})",
            f"Trip end ({tz})",
            "Duration",
            "Trip type",
            "Cavers",
            "Clubs",
            "Expedition",
            "Horizontal distance",
            "Vertical distance down",
            "Vertical distance up",
            "Surveyed distance",
            "Resurveyed distance",
            "Aid climbing distance",
            "Notes",
            "URL",
            "Trip report",
            f"Added on ({tz})",
            f"Last updated ({tz})",
        ]
    )

    # Content
    units = request.user.units  # Distance units
    tf = "%Y-%m-%d %H:%M"  # Time format to use
    x = 1
    for t in qs:
        row = [  # Break row into two to process end time
            x,
            t.cave_name,
            t.cave_region,
            t.cave_country,
            t.cave_url,
            lt(t.start).strftime(tf),
        ]

        # End time may not exist, so check first
        try:
            row = row + [lt(t.end).strftime(tf)]
        except AttributeError:
            row = row + [t.end]

        trip_report = ""
        if t.has_report:
            trip_report = f"https://caves.app{t.report.get_absolute_url()}"

        row = row + [  # Second half of row
            t.duration_str,
            t.type,
            t.cavers,
            t.clubs,
            t.expedition,
            distformat(t.horizontal_dist, units, simplify=False),
            distformat(t.vert_dist_down, units, simplify=False),
            distformat(t.vert_dist_up, units, simplify=False),
            distformat(t.surveyed_dist, units, simplify=False),
            distformat(t.resurveyed_dist, units, simplify=False),
            distformat(t.aid_dist, units, simplify=False),
            t.notes,
            f"https://caves.app{t.get_absolute_url()}",
            trip_report,
            lt(t.added).strftime(tf),
            lt(t.updated).strftime(tf),
        ]

        writer.writerow(row)  # Finally write the complete row
        x += 1

    return response  # Return the CSV file as a HttpResponse


@login_required
def user_statistics(request):
    """Show statistics for a user."""
    trips = request.user.trips
    chart_units = "m"
    if request.user.units == get_user_model().IMPERIAL:
        chart_units = "ft"

    # Generate stats for trips/distances by year
    this_year = timezone.now().year
    prev_year = (timezone.now() - timezone.timedelta(days=365)).year
    prev_year_2 = (timezone.now() - timezone.timedelta(days=730)).year
    trip_stats = statistics.stats_for_user(trips)
    trip_stats_year0 = statistics.stats_for_user(trips, year=prev_year_2)
    trip_stats_year1 = statistics.stats_for_user(trips, year=prev_year)
    trip_stats_year2 = statistics.stats_for_user(trips, year=this_year)

    # Check if we should show time charts
    show_time_charts = False
    if len(trips) >= 2:
        ordered = trips.order_by("-start")
        if (ordered.first().start.date() - ordered.last().start.date()).days > 40:
            if trips.filter(end__isnull=False):
                show_time_charts = True

    context = {
        "trips": trips,
        "gte_five_trips": len(trips) >= 5,
        "show_time_charts": show_time_charts,
        "user": request.user,
        "dist_format": request.user.units,
        "chart_units": chart_units,
        "year0": prev_year_2,
        "year1": prev_year,
        "year2": this_year,
        "trip_stats": trip_stats,
        "trip_stats_year0": trip_stats_year0,
        "trip_stats_year1": trip_stats_year1,
        "trip_stats_year2": trip_stats_year2,
        "common_caves": statistics.common_caves(trips),
        "common_cavers": statistics.common_cavers(trips),
        "common_cavers_by_time": statistics.common_cavers_by_time(trips),
        "common_clubs": statistics.common_clubs(trips),
        "most_duration": trips.exclude(duration=None).order_by("-duration")[0:10],
        "averages": statistics.trip_averages(trips, request.user.units),
        "most_vert_up": trips.filter(vert_dist_up__gt=0).order_by("-vert_dist_up")[
            0:10
        ],
        "most_vert_down": trips.filter(vert_dist_down__gt=0).order_by(
            "-vert_dist_down"
        )[0:10],
        "most_surveyed": trips.filter(surveyed_dist__gt=0).order_by("-surveyed_dist")[
            0:10
        ],
        "most_resurveyed": trips.filter(resurveyed_dist__gt=0).order_by(
            "-resurveyed_dist"
        )[0:10],
        "most_aid": trips.filter(aid_dist__gt=0).order_by("-aid_dist")[0:10],
        "most_horizontal": trips.filter(horizontal_dist__gt=0).order_by(
            "-horizontal_dist"
        )[0:10],
    }
    return render(request, "statistics.html", context)


def admin_tools(request):
    """Tools for website administrators."""
    if not request.user.is_superuser:
        raise Http404

    if request.POST:
        if request.POST["login_as"]:
            try:
                user = get_user_model().objects.get(email=request.POST["login_as"])
                if user.is_superuser:
                    messages.error(
                        request, "Cannot login as a superuser via this page."
                    )
                elif user:
                    messages.success(request, f"Now logged in as {user.email}.")
                    login(request, user)
                    return redirect("log:index")

            except ObjectDoesNotExist:
                messages.error(request, f"User was not found.")

    users = get_user_model().objects.all()
    active_users = users.filter(is_active=True)
    disabled_users = users.filter(is_active=False)
    prune_users = disabled_users.filter(
        date_joined__lt=timezone.now() - timezone.timedelta(days=1)
    )
    joined_year = users.filter(
        date_joined__gt=timezone.now() - timezone.timedelta(days=365)
    )
    joined_month = joined_year.filter(
        date_joined__gt=timezone.now() - timezone.timedelta(days=31)
    )
    joined_week = joined_month.filter(
        date_joined__gt=timezone.now() - timezone.timedelta(days=7)
    )
    joined_day = joined_week.filter(
        date_joined__gt=timezone.now() - timezone.timedelta(days=1)
    )

    trips = Trip.objects.all()
    trips_year = trips.filter(added__gt=timezone.now() - timezone.timedelta(days=365))
    trips_month = trips_year.filter(
        added__gt=timezone.now() - timezone.timedelta(days=31)
    )
    trips_week = trips_month.filter(
        added__gt=timezone.now() - timezone.timedelta(days=7)
    )
    trips_day = trips_week.filter(added__gt=timezone.now() - timezone.timedelta(days=1))

    login_user_list = active_users.values_list("email", flat=True)

    context = {
        "users": users,
        "active_users": active_users.order_by("-last_seen"),
        "disabled_users": disabled_users,
        "prune_users": prune_users.order_by("date_joined"),
        "joined_day": joined_day,
        "joined_week": joined_week,
        "joined_month": joined_month,
        "joined_year": joined_year,
        "trips": trips,
        "trips_day": trips_day,
        "trips_week": trips_week,
        "trips_month": trips_month,
        "trips_year": trips_year,
        "login_user_list": login_user_list,
    }

    return render(request, "admin_tools.html", context)


class TripListView(LoginRequiredMixin, ListView):
    """List all of a user's trips."""

    model = Trip
    template_name_suffix = "_list"
    paginate_by = 100
    ordering = ("-start", "pk")

    def get_queryset(self):
        """Only allow the user to update trips they created"""
        qs = Trip.objects.filter(user=self.request.user).select_related("report")
        return qs.order_by(*self.get_ordering())

    def get_ordering(self):
        """Allow sorting of the trip list table"""
        ordering = self.request.GET.get("sort", "")
        allowed_ordering = [
            "start",
            "cave_name",
            "duration",
            "type",
            "vert_dist_up",
            "vert_dist_down",
        ]
        print(ordering)
        if ordering.replace("-", "") in allowed_ordering:
            print(ordering)
            return (ordering, "pk")
        return self.ordering

    def get_context_data(self):
        """Add the trip 'index' dict to prevent many DB queries, as well as GET parameters"""
        context = super().get_context_data()
        context["trip_index"] = services.trip_index(self.request.user)
        parameters = self.request.GET.copy()
        parameters = parameters.pop("page", True) and parameters.urlencode()
        context["get_parameters"] = parameters
        return context


class TripUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """Update/edit a trip."""

    model = Trip
    form_class = TripForm
    template_name_suffix = "_update_form"
    success_message = "The trip has been updated."

    def get_queryset(self):
        """Only allow the user to update trips they created"""
        return Trip.objects.filter(user=self.request.user)


class TripDetailView(LoginRequiredMixin, DetailView):
    """View the details of a trip."""

    model = Trip

    def get_queryset(self):
        """Only allow non-superusers to view trips they created"""
        if self.request.user.is_superuser:
            return Trip.objects.all()
        else:
            return Trip.objects.filter(user=self.request.user).select_related("user")


class TripCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    """Create a new trip."""

    model = Trip
    form_class = TripForm
    template_name_suffix = "_create_form"
    success_message = "The trip has been created."
    initial = {
        "start": timezone.localdate(),
        "end": timezone.localdate(),
    }

    def form_valid(self, form):
        """Set the user to the current user"""
        candidate = form.save(commit=False)
        candidate.user = self.request.user
        candidate.save()
        return super().form_valid(form)

    def get_initial(self):
        """Set the cave_country field to the user's country"""
        initial = super(TripCreateView, self).get_initial()
        initial = initial.copy()
        initial["cave_country"] = self.request.user.country.name
        return initial

    def get_success_url(self):
        """If 'addanother' is set, redirect to the form again."""
        if self.request.POST.get("addanother", False):
            return reverse("log:trip_create")
        return super().get_success_url()


class TripDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a trip."""

    model = Trip
    template_name_suffix = "_delete"
    success_url = reverse_lazy("log:trip_list")

    def get_queryset(self):
        """Only allow the user to delete trips they created"""
        return Trip.objects.filter(user=self.request.user)

    def form_valid(self, form):
        """Provide a success message upon deletion."""
        response = super().form_valid(form)
        messages.success(self.request, "The trip has been deleted.")
        return response


class ReportCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    """Create a new trip report."""

    model = TripReport
    form_class = TripReportForm
    template_name_suffix = "_create_form"
    success_message = "The trip report has been created."
    initial = {
        "pub_date": timezone.localdate,
    }

    def form_valid(self, form):
        """Set the user and trip"""
        candidate = form.save(commit=False)
        candidate.user = self.request.user
        candidate.trip = self.get_trip()
        candidate.save()
        return super().form_valid(form)

    def get_context_data(self, *args, **kwargs):
        """Add the trip to the context"""
        context = super().get_context_data(*args, **kwargs)
        context["trip"] = self.get_trip()
        return context

    def get_trip(self):
        """Get the trip object and perform permissions checks"""
        trip = get_object_or_404(Trip, pk=self.kwargs["pk"])
        if not trip.user == self.request.user:
            raise Http404  # Users can only create reports for their own trips
        return trip

    def get(self, request, *args, **kwargs):
        """If the trip report already exists, redirect to the detail view"""
        trip = self.get_trip()
        if trip.has_report:
            return redirect(trip.report.get_absolute_url())

        return super().get(self, request, *args, **kwargs)

    def get_form_kwargs(self):
        """Pass the user to the form to validate the slug."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class ReportDetailView(LoginRequiredMixin, DetailView):
    """View the details of a trip report."""

    model = TripReport

    def get_queryset(self):
        """Only allow non-superusers to view reports they created"""
        if self.request.user.is_superuser:
            return TripReport.objects.all()
        else:
            return TripReport.objects.filter(user=self.request.user)

    def get_context_data(self, *args, **kwargs):
        """Add the trip to the context"""
        context = super().get_context_data(*args, **kwargs)
        context["trip"] = self.get_object().trip
        return context


class ReportUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """Update/edit a trip report."""

    model = TripReport
    form_class = TripReportForm
    template_name_suffix = "_update_form"
    success_message = "The trip report has been updated."

    def get_queryset(self):
        """Only allow the user to update reports they created"""
        return TripReport.objects.filter(user=self.request.user)

    def get_context_data(self, *args, **kwargs):
        """Add the trip to the context"""
        context = super().get_context_data(*args, **kwargs)
        context["trip"] = self.get_object().trip
        return context

    def get_form_kwargs(self):
        """Pass the user to the form to validate the slug."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class ReportDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a trip report."""

    model = TripReport
    template_name_suffix = "_delete"

    def get_queryset(self):
        """Only allow the user to delete reports they created"""
        return TripReport.objects.filter(user=self.request.user)

    def get_success_url(self):
        """Redirect to the trip detail view"""
        return self.get_object().trip.get_absolute_url()

    def get_context_data(self, *args, **kwargs):
        """Add the trip to the context"""
        context = super().get_context_data(*args, **kwargs)
        context["trip"] = self.get_object().trip
        return context

    def form_valid(self, form):
        """Provide a success message upon deletion."""
        response = super().form_valid(form)
        messages.success(self.request, "The trip report has been deleted.")
        return response
