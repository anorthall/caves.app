from django.urls import path

from . import charts

app_name = "charts"

urlpatterns = [
    path("stats-over-time/", charts.stats_over_time, name="stats_over_time"),
    path("hours-per-month/", charts.hours_per_month, name="hours_per_month"),
    path("trip-types/", charts.trip_types, name="trip_types"),
    path("trip-types-time/", charts.trip_types_time, name="trip_types_time"),
]
