import humanize
from django.db.models import Count
from django.contrib.gis.measure import Distance
from django.utils import timezone
from .models import Trip


def sort_comma_separated_list(qs, value, limit=10):
    """Sort a field that has a comma separated list of values from a QuerySet"""
    values = qs.values(value)
    common = {}
    for v in values:
        split_list = v[value].split(",")
        for split_value in split_list:
            trimmed = split_value.strip()
            if not trimmed:
                continue
            if trimmed in common:
                common[trimmed] += 1
            else:
                common[trimmed] = 1
    return sorted(common.items(), key=lambda x: x[1], reverse=True)[0:limit]


def stats_for_user(qs, year=None):
    """Get statistics of trips within a QuerySet, optionally by year"""
    if year:
        qs = qs.filter(start__year=year)

    # Initialise results
    results = {
        "vert_down": Distance(m=0),
        "vert_up": Distance(m=0),
        "surveyed": Distance(m=0),
        "resurveyed": Distance(m=0),
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
        results["resurveyed"] += trip.resurveyed_dist
        results["horizontal"] += trip.horizontal_dist
        results["aided"] += trip.aid_dist

    # Humanise duration
    results["time"] = humanize.precisedelta(
        results["time"], minimum_unit="hours", format="%.0f"
    )

    return results


def common_caves(qs, limit=10):
    """Get a list of the most common caves in a QuerySet"""
    return (
        qs.values("cave_name")
        .annotate(count=Count("cave_name"))
        .order_by("-count")[0:limit]
    )


def common_cavers(qs, limit=10):
    """Get a list of the most common cavers in a QuerySet"""
    return sort_comma_separated_list(qs, "cavers", limit)


def common_clubs(qs, limit=10):
    """Get a list of the most common clubs in a QuerySet"""
    return sort_comma_separated_list(qs, "clubs", limit)


def common_types(qs, limit=10):
    """Get a list of the most common types in a QuerySet"""
    return qs.values("type").annotate(count=Count("type")).order_by("-count")[0:limit]


def most_duration(qs, limit=10):
    """Get trips with the most duration from a QuerySet"""
    most_duration = {}
    for trip in qs:
        if trip.duration:
            most_duration[trip] = trip.duration
    results = sorted(most_duration.items(), key=lambda x: x[1], reverse=True)[0:limit]

    humanised_results = {}
    for trip, duration in results:
        humanised_results[trip] = humanize.precisedelta(
            duration, minimum_unit="minutes", format="%.0f"
        )
    return humanised_results.items()


def get_vertical_and_horizontal_count(qs):
    """Get the number of trips with vertical and horizontal distance"""
    vertical, horizontal = 0, 0
    for trip in qs:
        if trip.vert_dist_up or trip.vert_dist_down or trip.aid_dist:
            vertical += 1
        else:
            horizontal += 1
