from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
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
    return render(request, "index_registered.html")


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
    model = Trip
    template_name_suffix = "_list"
    paginate_by = 25

    def get_queryset(self):
        """Only allow the user to update trips they created"""
        qs = Trip.objects.filter(user=self.request.user).order_by("-start")
        return qs.select_related("user")


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
        return Trip.objects.filter(user=self.request.user).select_related("user")


class TripCreateView(LoginRequiredMixin, CreateView):
    model = Trip
    form_class = TripForm
    template_name_suffix = "_create_form"
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
    model = Trip
    template_name_suffix = "_delete"
    success_url = reverse_lazy("log:trip_list")

    def get_queryset(self):
        """Only allow the user to delete trips they created"""
        return Trip.objects.filter(user=self.request.user)


@login_required
def trip_deleted(request):
    messages.info(request, "The trip has been deleted.")
    return redirect("log:index")
