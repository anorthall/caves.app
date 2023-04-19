from datetime import timedelta as td

from django.contrib.auth.decorators import login_required
from django.contrib.gis.measure import D
from django.http import JsonResponse
from django.utils import timezone
from users.models import UserSettings

from .models import Trip


def _use_units(value, units):
    if units == UserSettings.IMPERIAL:
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
        for trip in qs:
            if trip.start >= cur_date and trip.start < cur_date + td(days=7):
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
        vert_up.append(_use_units(accum_vert_up, request.user.settings.units))
        vert_down.append(_use_units(accum_vert_down, request.user.settings.units))
        surveyed.append(_use_units(accum_surveyed, request.user.settings.units))
        resurveyed.append(_use_units(accum_resurveyed, request.user.settings.units))
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


@login_required
def trip_types(request):
    """JSON data for a chart showing trip types"""
    qs = Trip.objects.filter(user=request.user)
    result = {}
    for trip in qs:
        if trip.type not in result:
            result[trip.type] = 1
        else:
            result[trip.type] += 1
    result = dict(sorted(result.items(), key=lambda item: item[1], reverse=True))
    labels, data = [], []
    for k, v in result.items():
        labels.append(k)
        data.append(v)

    return JsonResponse(data={"labels": labels, "data": data})


@login_required
def trip_types_time(request):
    """JSON data for a chart showing trip types by time"""
    qs = Trip.objects.filter(user=request.user)
    result = {}
    for trip in qs:
        if trip.end:
            if trip.type not in result:
                result[trip.type] = trip.duration
            else:
                result[trip.type] += trip.duration

    result = dict(sorted(result.items(), key=lambda item: item[1], reverse=True))
    labels, data = [], []
    for k, v in result.items():
        result[k] = v.total_seconds() / 60 / 60
        labels.append(k)
        data.append(result[k])

    return JsonResponse(data={"labels": labels, "data": data})


@login_required
def hours_per_month(request):
    """JSON data for a chart showing hours per month"""
    qs = Trip.objects.filter(user=request.user)
    labels = []
    data = []
    today = timezone.now()
    start_date = (today - td(days=(365 * 2))).replace(day=1)
    cur_date = start_date

    while cur_date <= today:
        next_date = (cur_date + td(days=32)).replace(day=1)
        labels.append(cur_date.strftime("%b %y"))
        month_hours = 0
        for trip in qs:
            if trip.start >= cur_date and trip.start < next_date:
                if trip.duration:
                    month_hours += trip.duration.total_seconds() / 3600
        data.append(month_hours)
        cur_date = next_date

    return JsonResponse(data={"labels": labels, "data": data})
