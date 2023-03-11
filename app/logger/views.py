from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView, DetailView, CreateView
from django.http import HttpResponseRedirect
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
    # Get a list of trips by the current user
    trips = Trip.objects.filter(user=request.user).order_by("-trip_start")

    context = {
        "user": request.user,
        "trips": trips,
    }
    return render(request, "index.html", context)


class TripUpdateView(LoginRequiredMixin, UpdateView):
    model = Trip
    form_class = TripForm
    template_name_suffix = "_update_form"

    def get_queryset(self):
        """Only allow the user to update trips they created"""
        return Trip.objects.filter(user=self.request.user)


class TripDetailView(LoginRequiredMixin, DetailView):
    model = Trip

    def get_queryset(self):
        """Only allow the user to view trips they created"""
        return Trip.objects.filter(user=self.request.user)


class TripCreateView(LoginRequiredMixin, CreateView):
    model = Trip
    form_class = TripForm
    template_name_suffix = "_create_form"

    def form_valid(self, form):
        """Set the user to the current user"""
        candidate = form.save(commit=False)
        candidate.user = self.request.user
        candidate.save()
        return super().form_valid(form)
