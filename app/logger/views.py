from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import (
    UpdateView,
    DetailView,
    CreateView,
    DeleteView,
    ListView,
)
from django.utils import timezone
from .models import Trip
from .forms import TripForm


def index(request):
    """
    Index page for the entire website

    Unregistered users will be shown a static welcome page

    Registered users will be shown an interface to add/manage
    recent caving trips.
    """

    # Unregistered/unauthenticated users
    if not request.user.is_authenticated:
        return redirect("users:login")

    # Authenticated users
    # Get most recent trips
    qs = Trip.objects.filter(user=request.user).order_by("-start")
    recent_trips = qs[:6]
    trip_count = qs.count()
    site_trip_count = Trip.objects.all().count()

    # Only display 3 or 6 trips
    if recent_trips.count() < 3:
        # Display welcome text until the user has created three trips
        recent_trips = None
    elif recent_trips.count() == 4 or recent_trips.count() == 5:
        recent_trips = recent_trips[:3]  # Display only three trips

    context = {
        "recent_trips": recent_trips,
        "trip_count": trip_count,
        "site_trip_count": site_trip_count,
        "stats": request.user.get_trip_stats(),
        "stats_year": request.user.get_trip_stats(year=timezone.now().year),
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


class TripListView(LoginRequiredMixin, ListView):
    """List all of a user's trips."""

    model = Trip
    template_name_suffix = "_list"
    paginate_by = 25

    def get_queryset(self):
        """Only allow the user to update trips they created"""
        qs = Trip.objects.filter(user=self.request.user).order_by("-start")
        return qs.select_related("user")

    def get_context_data(self):
        """Add the trip 'index' dict to prevent many DB queriers"""
        context = super().get_context_data()
        context["trip_index"] = Trip.trip_index(self.request.user)
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
