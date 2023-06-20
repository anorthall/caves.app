from django.urls import path

from . import views

app_name = "stats"

urlpatterns = [
    path("", views.Index.as_view(), name="index"),
    path(
        "charts/<slug:username>/stats-over-time/",
        views.chart_stats_over_time,
        name="chart_stats_over_time",
    ),
    path(
        "charts/<slug:username>/hours-per-month/",
        views.chart_hours_per_month,
        name="chart_hours_per_month",
    ),
    path("charts/trip-types/", views.chart_trip_types, name="chart_trip_types"),
    path(
        "charts/trip-types-time/",
        views.chart_trip_types_time,
        name="chart_trip_types_time",
    ),
]
