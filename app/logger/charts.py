from datetime import timedelta as td
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

    # Generate labels
    first_trip = qs.first().start
    last_trip = qs.last().start
    cur_date = first_trip
    while cur_date <= last_trip:
        labels.append(cur_date.strftime("%Y-%m-%d"))
        week_duration = 0
        week_vert_up = D(m=0)
        week_vert_down = D(m=0)
        week_surveyed = D(m=0)
        week_resurveyed = D(m=0)
        for trip in qs.filter(start__gte=cur_date, start__lt=cur_date + td(days=7)):
            if trip.duration:
                week_duration += trip.duration.total_seconds() / 60 / 60
            if trip.vert_dist_up:
                week_vert_up += trip.vert_dist_up
            if trip.vert_dist_down:
                week_vert_down += trip.vert_dist_down
            if trip.surveyed_dist:
                week_surveyed += trip.surveyed_dist
            if trip.resurveyed_dist:
                week_resurveyed += trip.resurveyed_dist
        accum_duration += week_duration
        accum_vert_up += week_vert_up
        accum_vert_down += week_vert_down
        accum_surveyed += week_surveyed
        accum_resurveyed += week_resurveyed
        duration.append(accum_duration)
        vert_up.append(use_units(accum_vert_up, request.user.units))
        vert_down.append(use_units(accum_vert_down, request.user.units))
        surveyed.append(use_units(accum_surveyed, request.user.units))
        resurveyed.append(use_units(accum_resurveyed, request.user.units))
        cur_date += td(days=7)

    data = {
        "labels": labels,
    }

    # Check for blank datasets and don't add them to the response
    for x in ["duration", "vert_up", "vert_down", "surveyed", "resurveyed"]:
        add = False
        for y in locals()[x]:
            if y != 0:
                add = True
                break
        if add:
            data[x] = locals()[x]

    return JsonResponse(data=data)
