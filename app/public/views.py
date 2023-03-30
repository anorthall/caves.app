from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.utils import timezone
from django.utils.timezone import timedelta
from django.http import Http404
from django.contrib.auth import get_user_model
from logger import statistics
from logger.models import Trip, TripReport


def user(request, username):
    """View the public profile for a user."""
    user = get_object_or_404(get_user_model(), username=username)
    if not user.privacy == get_user_model().PUBLIC:
        raise Http404  # No public profile allowed

    # Get the QuerySets.
    all_trips = Trip.objects.filter(user=user)

    # Public trips. We know that the user is set to Public as we tested that above,
    # so 'Default' privacy must be acceptable.
    public_trips = all_trips.filter(
        Q(privacy="Public") | Q(privacy="Default")
    ).prefetch_related("user")

    # Generate stats.
    this_year = timezone.now().year
    prev_year = (timezone.now() - timedelta(days=365)).year
    trip_stats = statistics.stats_for_user(user)
    trip_stats_year1 = statistics.stats_for_user(user, year=prev_year)
    trip_stats_year2 = statistics.stats_for_user(user, year=this_year)

    context = {
        "user": user,
        "trips": public_trips.order_by("-start", "pk"),
        "dist_format": user.units,
        "year1": prev_year,
        "year2": this_year,
        "trip_stats": trip_stats,
        "trip_stats_year1": trip_stats_year1,
        "trip_stats_year2": trip_stats_year2,
    }
    return render(request, "user.html", context)


def trip(request, username, pk):
    """View a public trip."""
    trip = get_object_or_404(Trip, pk=pk)
    if trip.user.username != username:
        raise Http404

    if not trip.is_public:
        raise Http404  # Private trip

    context = {
        "trip": trip,
        "user": trip.user,
        "user_is_public": trip.user.is_public,
    }
    return render(request, "trip.html", context)


def tripreport(request, username, slug):
    """View a public trip report."""
    report = get_object_or_404(TripReport, user__username=username, slug=slug)
    if not report.is_public:
        raise Http404

    context = {
        "report": report,
        "user": report.user,
        "trip": report.trip,
        "trip_is_public": report.trip.is_public,
        "user_is_public": report.user.is_public,
    }

    return render(request, "tripreport.html", context)
