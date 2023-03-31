from django.urls import path
from . import charts

app_name = "charts"

urlpatterns = [
    path("duration/", charts.stats_over_time, name="stats_over_time"),
    path("trip-types/", charts.trip_types, name="trip_types"),
    path("trip-types-time/", charts.trip_types_time, name="trip_types_time"),
]
