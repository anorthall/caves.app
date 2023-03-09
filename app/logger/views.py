from django.shortcuts import render
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView, DetailView
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
        return render(request, "index_unregistered.html")

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
    success_url = reverse_lazy("log:index")
    template_name_suffix = "_update_form"

    def get_queryset(self):
        return Trip.objects.filter(user=self.request.user)


class TripDetailView(LoginRequiredMixin, DetailView):
    model = Trip

    def get_queryset(self):
        return Trip.objects.filter(user=self.request.user)
