from typing import Union

from attrs import frozen
from django.contrib.gis.measure import D
from django.db import models
from django.utils import timezone


@frozen
class Row:
    metric: str
    value: Union[str, D]
    is_dist: bool = False
    is_time: bool = False


def averages(queryset, disable_dist_stats=False, disable_survey_stats=False):
    rows = [
        Row(metric="Trips per week", value=trips_per_week(queryset)),
        Row(metric="Trip duration", value=trip_duration(queryset), is_time=True),
    ]

    if not disable_dist_stats:
        rows += [
            Row(
                metric="Rope climbed",
                value=dist(queryset, "vert_dist_up"),
                is_dist=True,
            ),
            Row(
                metric="Rope descended",
                value=dist(queryset, "vert_dist_down"),
                is_dist=True,
            ),
            Row(metric="Aid climbed", value=dist(queryset, "aid_dist"), is_dist=True),
            Row(
                metric="Horizontal",
                value=dist(queryset, "horizontal_dist"),
                is_dist=True,
            ),
        ]

    if not disable_survey_stats:
        rows += [
            Row(metric="Surveyed", value=dist(queryset, "surveyed_dist"), is_dist=True),
            Row(
                metric="Resurveyed",
                value=dist(queryset, "resurveyed_dist"),
                is_dist=True,
            ),
        ]

    # Clear out any rows with a zero value
    return [row for row in rows if row.value]


def trips_per_week(queryset):
    if not queryset.exists():  # pragma: no cover
        return 0

    qs = queryset.order_by("start")
    weeks = (timezone.now() - qs.first().start).days // 7

    return 0 if weeks == 0 else qs.count() / weeks


def trip_duration(queryset):
    qs = queryset.filter(end__isnull=False)
    if qs.count() == 0:
        return 0

    return qs.aggregate(avg_duration=models.Avg("duration"))["avg_duration"]


def dist(queryset, field):
    """Get the average distance for a field, excluding trips with a zero value"""
    qs = queryset.filter(**{f"{field}__gt": 0})
    if qs.count() == 0:
        return D(m=0)

    avg_meters = qs.aggregate(avg_dist=models.Avg(field))["avg_dist"]
    return D(m=avg_meters)
