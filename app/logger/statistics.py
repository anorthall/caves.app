from .models import Trip
from django.contrib.gis.measure import Distance
from django.utils import timezone
from django.core.exceptions import ValidationError
import humanize


def stats_for_user(qs, year=None):
    """Get statistics of trips within a QuerySet, optionally by year"""
    if year:
        qs = qs.filter(start__year=year)

    # Initialise results
    results = {
        "vert_down": Distance(m=0),
        "vert_up": Distance(m=0),
        "surveyed": Distance(m=0),
        "aided": Distance(m=0),
        "horizontal": Distance(m=0),
        "trips": 0,
        "time": timezone.timedelta(0),
    }

    # Return the empty results if there are no trips.
    if not bool(qs):
        results["time"] = "0"
        return results

    # Iterate and add up
    for trip in qs:
        if trip.type == Trip.SURFACE:
            continue  # Don't count surface trips
        results["trips"] += 1
        results["time"] += trip.duration if trip.end else timezone.timedelta(0)
        results["vert_down"] += trip.vert_dist_down
        results["vert_up"] += trip.vert_dist_up
        results["surveyed"] += trip.surveyed_dist
        results["horizontal"] += trip.horizontal_dist
        results["aided"] += trip.aid_dist

    # Humanise duration
    results["time"] = humanize.precisedelta(
        results["time"], minimum_unit="hours", format="%.0f"
    )

    return results


def __str__(self):
    """Return the name of the cave visited."""
    return self.cave_name


def clean(self):
    """Check that the start is before the end"""
    # Check self.start exists - may have been removed by form validation
    # If it does not exist 'for real', the form/low level model validation will catch it.
    if self.start and self.end:
        if self.start > self.end:
            raise ValidationError(
                "The trip start time must be before the trip end time."
            )
