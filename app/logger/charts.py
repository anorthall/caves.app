from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.gis.measure import D
from django.http import JsonResponse
from .models import Trip


def use_units(value, units):
    if units == get_user_model().IMPERIAL:
        return value.ft
    else:
        return value.m


@login_required
def stats_over_time(request):
    """JSON data for a chart showing stats over time"""
    qs = Trip.objects.filter(user=request.user).order_by("start")
    labels, duration, vert_down, vert_up, surveyed, resurveyed = [], [], [], [], [], []
    accum_duration = 0
    accum_vert_up = D(m=0)
    accum_vert_down = D(m=0)
    accum_surveyed = D(m=0)
    accum_resurveyed = D(m=0)

    for trip in qs:
        labels.append(trip.start.strftime("%Y-%m-%d"))
        if trip.duration:
            accum_duration += trip.duration.total_seconds() / 60 / 60
        duration.append(accum_duration)

        if trip.vert_dist_up:
            accum_vert_up += trip.vert_dist_up
        vert_up.append(use_units(accum_vert_up, request.user.units))

        if trip.vert_dist_down:
            accum_vert_down += trip.vert_dist_down
        vert_down.append(use_units(accum_vert_down, request.user.units))

        if trip.surveyed_dist:
            accum_surveyed += trip.surveyed_dist
        surveyed.append(use_units(accum_surveyed, request.user.units))

        if trip.resurveyed_dist:
            accum_resurveyed += trip.resurveyed_dist
        resurveyed.append(use_units(accum_resurveyed, request.user.units))

    return JsonResponse(
        data={
            "labels": labels,
            "duration": duration,
            "vert_up": vert_up,
            "vert_down": vert_down,
            "surveyed": surveyed,
            "resurveyed": resurveyed,
        }
    )
