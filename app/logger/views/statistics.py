from core.utils import get_user
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from django.utils.safestring import SafeString
from users.models import CavingUser as User

from .. import statistics


@login_required
def user_statistics(request):
    trips = get_user(request).trips
    chart_units = "m"
    if request.units == User.IMPERIAL:
        chart_units = "ft"

    # Generate stats for trips/distances by year
    this_year = timezone.now().year
    prev_year = (timezone.now() - timezone.timedelta(days=365)).year
    prev_year_2 = (timezone.now() - timezone.timedelta(days=730)).year
    trip_stats = statistics.stats_for_user(trips)
    trip_stats_year0 = statistics.stats_for_user(trips, year=prev_year_2)
    trip_stats_year1 = statistics.stats_for_user(trips, year=prev_year)
    trip_stats_year2 = statistics.stats_for_user(trips, year=this_year)

    # Check if we should show time charts
    show_time_charts = False
    if len(trips) >= 2:
        ordered = trips.order_by("-start")
        if (ordered.first().start.date() - ordered.last().start.date()).days > 40:
            if trips.filter(end__isnull=False):
                show_time_charts = True

    if len(trips) < 5:
        messages.warning(
            request,
            "Full featured statistics are not available as you have added "
            "less than five trips.",
        )

    context = {
        "trips": trips,
        "gte_five_trips": len(trips) >= 5,
        "show_time_charts": show_time_charts,
        "user": request.user,
        "chart_units": chart_units,
        "year0": prev_year_2,
        "year1": prev_year,
        "year2": this_year,
        "trip_stats": trip_stats,
        "trip_stats_year0": trip_stats_year0,
        "trip_stats_year1": trip_stats_year1,
        "trip_stats_year2": trip_stats_year2,
        "common_caves": statistics.common_caves(trips),
        "common_cavers": statistics.common_cavers(trips),
        "common_cavers_by_time": statistics.common_cavers_by_time(trips),
        "common_clubs": statistics.common_clubs(trips),
        "most_duration": trips.exclude(duration=None).order_by("-duration")[0:10],
        "averages": statistics.trip_averages(trips, get_user(request).units),
        "most_vert_up": trips.filter(vert_dist_up__gt=0).order_by("-vert_dist_up")[
            0:10
        ],
        "most_vert_down": trips.filter(vert_dist_down__gt=0).order_by(
            "-vert_dist_down"
        )[0:10],
        "most_surveyed": trips.filter(surveyed_dist__gt=0).order_by("-surveyed_dist")[
            0:10
        ],
        "most_resurveyed": trips.filter(resurveyed_dist__gt=0).order_by(
            "-resurveyed_dist"
        )[0:10],
        "most_aid": trips.filter(aid_dist__gt=0).order_by("-aid_dist")[0:10],
        "most_horizontal": trips.filter(horizontal_dist__gt=0).order_by(
            "-horizontal_dist"
        )[0:10],
    }

    new_version_msg = SafeString(
        "A new version of the statistics page is under development. You can "
        'view it by <a href="/stats/">clicking here</a>.'
    )
    messages.info(request, new_version_msg)
    return render(request, "logger/statistics.html", context)
