import csv
from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
from django.utils import timezone
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
from .models import Trip
from .forms import TripForm


def index(request):
    """
    Index page for the entire website

    Unregistered users will be shown a static welcome page

    Registered users will be shown an interface to add/manage
    recent caving trips.
    """
    if not request.user.is_authenticated:
        return redirect("users:login")

    # Get most recent trips
    qs = Trip.objects.filter(user=request.user).order_by("-start")
    recent_trips = qs[:6]
    trip_count = qs.count()
    recent_trip_count = recent_trips.count()

    # Only display 3 or 6 trips
    if recent_trip_count < 3:
        # Display welcome text until the user has created three trips
        recent_trips = None
    elif recent_trip_count == 4 or recent_trip_count == 5:
        recent_trips = recent_trips[:3]  # Display only three trips

    # Distance stats
    trip_stats = Trip.stats_for_user(request.user)
    trip_stats_year = Trip.stats_for_user(request.user, year=timezone.now().year)

    context = {
        "recent_trips": recent_trips,
        "trip_count": trip_count,
        "trip_stats": trip_stats,
        "trip_stats_year": trip_stats_year,
        "dist_format": request.user.units,
    }
    return render(request, "index_registered.html", context)


def about(request):
    """About page, rendering differently depending whether the user is logged in or not"""

    context = {
        "trip_count": Trip.objects.all().count(),
        "user_count": get_user_model().objects.all().count(),
    }

    # Unregistered/unauthenticated users
    if not request.user.is_authenticated:
        return render(request, "about/about_unregistered.html", context)

    # Authenticated users
    return render(request, "about/about_registered.html", context)


@login_required
def export(request):
    """Export a user's trips to CSV file"""
    if not request.POST:  # Display information page
        return render(request, "export.html")

    # Generate HTTP response and the CSV file
    qs = Trip.objects.filter(user=request.user).order_by("start")
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
    writer.writerow(
        [
            "Number",
            "Cave name",
            "Cave region",
            "Cave country",
            "Cave URL",
            "Trip start",
            "Trip end",
            "Duration",
            "Trip type",
            "Cavers",
            "Clubs",
            "Expedition",
            "Horizontal distance",
            "Vertical distance down",
            "Vertical distance up",
            "Surveyed distance",
            "Aid climbing distance",
            "Trip report",
            "Notes",
            "Added on",
            "Last updated",
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
            t.start.strftime(tf),
        ]

        # End time may not exist, so check first
        try:
            row = row + [t.end.strftime(tf)]
        except AttributeError:
            row = row + [t.end]

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
            distformat(t.aid_dist, units, simplify=False),
            t.report_url,
            t.notes,
            t.added.strftime(tf),
            t.updated.strftime(tf),
        ]

        writer.writerow(row)  # Finally write the complete row
        x += 1

    return response  # Return the CSV file as a HttpResponse


class TripListView(LoginRequiredMixin, ListView):
    """List all of a user's trips."""

    model = Trip
    template_name_suffix = "_list"
    paginate_by = 100

    def get_queryset(self):
        """Only allow the user to update trips they created"""
        qs = Trip.objects.filter(user=self.request.user).order_by("-start")
        return qs.select_related("user")

    def get_context_data(self):
        """Add the trip 'index' dict to prevent many DB queriers"""
        context = super().get_context_data()
        context["trip_index"] = Trip.trip_index(self.request.user)
        return context


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

    # Build user list
    qs = get_user_model().objects.filter(is_active=True, is_superuser=False)
    user_list = []
    for user in qs:
        user_list.append(user.email)

    # Build context
    context = {"user_list": user_list}

    return render(request, "admin_tools.html", context)


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
