import humanize
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.shortcuts import render
from logger.models import Trip
from .models import FAQ


def about(request):
    """About page, rendering differently depending on whether the user is logged in or not."""

    total_duration = timezone.timedelta(0)
    for trip in Trip.objects.all():
        if trip.duration:
            total_duration += trip.duration
    total_duration = humanize.precisedelta(
        total_duration, minimum_unit="hours", format="%.0f"
    )

    context = {
        "trip_count": Trip.objects.all().count(),
        "user_count": get_user_model().objects.all().count(),
        "total_duration": total_duration,
        "registered": request.user.is_authenticated,
    }

    # Unregistered/unauthenticated users
    if not request.user.is_authenticated:
        return render(request, "about/about_unregistered.html", context)

    # Authenticated users
    return render(request, "about/about_registered.html", context)


def help(request):
    """Help page, rendering differently depending on whether the user is logged in or not."""
    context = {"faqs": FAQ.objects.all().order_by("updated")}

    # Unregistered/unauthenticated users
    if not request.user.is_authenticated:
        return render(request, "help/help_unregistered.html", context)

    # Authenticated users
    return render(request, "help/help_registered.html", context)
