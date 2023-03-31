import humanize
from django.db.models import Count
from django.contrib.auth import get_user_model
from django.contrib.gis.measure import Distance, D
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


def vertical_and_horizontal_count(qs):
    """Get the number of trips with vertical and horizontal distance"""
    vertical, horizontal = 0, 0
    for trip in qs:
        if trip.vert_dist_up or trip.vert_dist_down or trip.aid_dist:
            vertical += 1
        else:
            horizontal += 1
    return vertical, horizontal


def trip_averages(qs, units):
    """Get the average distances in a QuerySet"""
    results = {
        "Rope climbed per trip": Distance(m=0),
        "Rope descended per trip": Distance(m=0),
        "Surveyed per trip": Distance(m=0),
        "Resurveyed per trip": Distance(m=0),
        "Aid climbed per trip": Distance(m=0),
        "Horizontal distance per trip": Distance(m=0),
        "Time underground per trip": timezone.timedelta(0),
    }
    survey_trips = 0
    survey_hours = 0
    vert_trips = 0
    vert_hours = 0
    for trip in qs:  # Add up
        results["Time underground per trip"] += (
            trip.duration if trip.end else timezone.timedelta(0)
        )
        results["Rope climbed per trip"] += (
            trip.vert_dist_up if trip.vert_dist_up else D()
        )
        results["Rope descended per trip"] += (
            trip.vert_dist_down if trip.vert_dist_down else D()
        )
        results["Surveyed per trip"] += (
            trip.surveyed_dist if trip.surveyed_dist else D()
        )
        results["Resurveyed per trip"] += (
            trip.resurveyed_dist if trip.resurveyed_dist else D()
        )
        results["Aid climbed per trip"] += trip.aid_dist if trip.aid_dist else D()
        results["Horizontal distance per trip"] += (
            trip.horizontal_dist if trip.horizontal_dist else D()
        )
        if trip.surveyed_dist > D(0) or trip.resurveyed_dist > D(0):
            survey_trips += 1
            if trip.duration:
                survey_hours += trip.duration.total_seconds() / 3600
        if trip.vert_dist_up > D() or trip.vert_dist_down > D() or trip.aid_dist > D():
            vert_trips += 1
            if trip.duration:
                vert_hours += trip.duration.total_seconds() / 3600

    climbed, descended = (
        results["Rope climbed per trip"],
        results["Rope descended per trip"],
    )
    total_hours = results["Time underground per trip"].total_seconds() / 3600
    total_survey = results["Surveyed per trip"] + results["Resurveyed per trip"]
    surveyed, resurveyed = results["Surveyed per trip"], results["Resurveyed per trip"]
    for key, value in results.items():  # Divide by number of trips
        if value:
            results[key] = value / qs.count()

    results["Rope climbed per trip*"] = climbed / vert_trips
    results["Rope descended per trip*"] = descended / vert_trips
    results["Rope climbed per hour"] = climbed / total_hours
    results["Rope descended per hour"] = descended / total_hours
    results["Rope climbed per hour*"] = climbed / vert_hours
    results["Rope descended per hour*"] = descended / vert_hours

    results["Surveyed per hour"] = surveyed / total_hours
    results["Resurveyed per hour"] = resurveyed / total_hours
    results["Surveyed** per hour***"] = total_survey / survey_hours

    results["Surveyed per trip***"] = surveyed / survey_trips
    results["Surveyed** per trip***"] = total_survey / survey_trips

    processed_results = {}
    for key, value in results.items():
        if value:
            if type(value) == timezone.timedelta:
                value = humanize.precisedelta(
                    value, minimum_unit="minutes", format="%.0f"
                )
            elif type(value) == Distance:
                if units == get_user_model().IMPERIAL:
                    processed_results[key] = f"{round(value.ft, 2)}ft"
                else:
                    processed_results[key] = f"{round(value.m, 2)}m"

    first_trip = qs.order_by("start").first().start
    last_trip = qs.order_by("-start").first().start
    weeks = (last_trip - first_trip).days / 7
    processed_results["Trips per week"] = round(qs.count() / weeks, 2)
    return sorted(processed_results.items())
