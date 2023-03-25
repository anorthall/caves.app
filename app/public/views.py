from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.views.generic import DetailView
from django.http import Http404
from django.contrib.auth import get_user_model
from logger.models import Trip


def user(request, username):
    """View the public profile for a user."""
    user = get_object_or_404(get_user_model(), username=username)
    if user.privacy == get_user_model().PRIVATE:
        raise Http404  # No public profile allowed

    # Get the QuerySet. Only accept trips with 'Public' or 'Default' privacy. We know that
    # the user is set to Public as we tested that above, so 'Default' privacy must be acceptable.
    trips = Trip.objects.filter(
        Q(user=user), Q(privacy="Public") | Q(privacy="Default")
    )
    context = {"user": user, "trips": trips.order_by("-start")}
    return render(request, "user.html", context)


def trip(request, username, pk):
    """View a public trip."""
    trip = get_object_or_404(Trip, pk=pk)
    if not trip.is_public:
        raise Http404  # Private trip

    context = {
        "trip": trip,
        "user": trip.user,
        "user_is_public": trip.user.is_public,
    }
    return render(request, "trip.html", context)
