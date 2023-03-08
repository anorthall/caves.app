from django.shortcuts import render, redirect
from .models import Trip


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
