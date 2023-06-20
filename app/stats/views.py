from datetime import timedelta as td

from core.utils import get_user
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.gis.measure import D
from django.http import JsonResponse
from django.utils import timezone
from django.views.generic import TemplateView
from logger.models import Trip

from . import statistics
from .services import match_and_check_username, use_units


class Index(LoginRequiredMixin, TemplateView):
    template_name = "stats/index.html"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.queryset = None

    def setup(self, *args, **kwargs):
        super().setup(*args, **kwargs)
        self.queryset = self.get_queryset()

    def get_context_data(self, *args, **kwargs):
        user = get_user(self.request)
        disable_dist = user.disable_distance_statistics
        disable_survey = user.disable_survey_statistics

        context = super().get_context_data(**kwargs)
        context["stats_yearly"] = statistics.yearly(self.queryset)
        context["stats_most_common"] = statistics.most_common(self.queryset)
        context["stats_biggest_trips"] = statistics.biggest_trips(
            self.queryset,
            limit=10,
            disable_dist_stats=disable_dist,
            disable_survey_stats=disable_survey,
        )
        context["stats_averages"] = statistics.averages(
            self.queryset,
            disable_dist_stats=disable_dist,
            disable_survey_stats=disable_survey,
        )
        context["stats_metrics"] = statistics.metrics(self.queryset)
        return context

    def get_queryset(self):
        return get_user(self.request).trips.exclude(type=Trip.SURFACE)


@login_required
def chart_stats_over_time(request, username):
    """
    JSON data for a chart showing stats over time

    We will iterate through every week between the user's first and last trip, add
    up the stats for that week, and then add them to separate lists. These lists will
    be used by chart.js to generate the chart.
    """
    user = match_and_check_username(request, username)
    qs = Trip.objects.filter(user=user).exclude(type=Trip.SURFACE).order_by("start")

    # These lists will contain one value for each week. The labels list will contain
    # the date for each week, and the other lists will contain the accumulated stats
    # for that week.
    labels, duration, vert_down, vert_up, surveyed, resurveyed = [], [], [], [], [], []

    # These variables will contain the accumulated stats for the current week, to be
    # added to the lists above.
    accum_duration, accum_vert_up, accum_vert_down, accum_surveyed = 0, D(), D(), D()
    accum_resurveyed = D()

    first_trip = qs.first().start
    last_trip = qs.last().start
    cur_date = first_trip

    while cur_date <= last_trip:
        # Variables to hold the totals for the current week
        week_duration, week_vert_up, week_vert_down = (
            0,
            D(),
            D(),
        )
        week_surveyed, week_resurveyed = D(), D()

        # Iterate through the trips and select the ones that fall within the current
        # week, and then add their stats to the totals for the week.
        for trip in qs:
            if cur_date <= trip.start < cur_date + td(days=7):
                if trip.duration:  # Ensure trip.duration != None
                    week_duration += trip.duration.total_seconds() / 60 / 60

                week_vert_up += trip.vert_dist_up
                week_vert_down += trip.vert_dist_down
                week_surveyed += trip.surveyed_dist
                week_resurveyed += trip.resurveyed_dist

        # Update the accumulators
        accum_duration += week_duration
        accum_vert_up += week_vert_up
        accum_vert_down += week_vert_down
        accum_surveyed += week_surveyed
        accum_resurveyed += week_resurveyed

        # Append the new data to the lists to be processed by chart.js
        labels.append(cur_date.strftime("%Y-%m-%d"))
        duration.append(accum_duration)
        vert_up.append(use_units(accum_vert_up, get_user(request).units))
        vert_down.append(use_units(accum_vert_down, get_user(request).units))
        surveyed.append(use_units(accum_surveyed, get_user(request).units))
        resurveyed.append(use_units(accum_resurveyed, get_user(request).units))

        # Finally, increment the current date by one week
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
def chart_hours_per_month(request, username):
    """JSON data for a chart showing hours per month"""
    user = match_and_check_username(request, username)
    qs = Trip.objects.filter(user=user).exclude(type=Trip.SURFACE).order_by("start")

    # Each of labels and data will contain one value for each month
    labels = []
    data = []

    # Start at the beginning of the month two years ago
    today = timezone.now()
    start_date = (today - td(days=(365 * 2))).replace(day=1)

    # Iterate through the months, adding the total hours for each month to the data
    cur_date = start_date
    while cur_date <= today:
        start_of_next_month = (cur_date + td(days=32)).replace(day=1)

        month_hours = 0
        for trip in qs:
            if cur_date <= trip.start < start_of_next_month:
                if trip.duration:
                    month_hours += trip.duration.total_seconds() / 3600

        labels.append(cur_date.strftime("%b %y"))
        data.append(month_hours)

        cur_date = start_of_next_month

    return JsonResponse(data={"labels": labels, "data": data})


@login_required
def chart_trip_types(request):  # TODO: Refactor and add to template
    """JSON data for a chart showing trip types"""
    qs = (
        Trip.objects.filter(user=request.user)
        .exclude(type=Trip.SURFACE)
        .order_by("start")
    )
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
def chart_trip_types_time(request):  # TODO: Refactor and add to template
    """JSON data for a chart showing trip types by time"""
    qs = (
        Trip.objects.filter(user=request.user)
        .exclude(type=Trip.SURFACE)
        .order_by("start")
    )
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
