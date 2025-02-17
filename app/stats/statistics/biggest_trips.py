from datetime import timedelta

from attrs import Factory, define, frozen
from distancefield import D
from logger.models import Trip


@frozen
class TripStatsRow:
    trip: Trip
    value: D | timedelta
    is_time: bool = False


@define
class TripStats:
    title: str
    metric: str
    rows: list = Factory(list)

    def add_row(self, trip, value, is_time=False):
        self.rows.append(TripStatsRow(trip=trip, value=value, is_time=is_time))


def _build_trip_stats(queryset, title, field, limit, metric=None, is_time=False):
    if metric is None:
        metric = title

    stats = TripStats(title=title, metric=metric)
    qs = queryset.exclude(**{field: None}).order_by("-" + field)[:limit]

    for trip in qs:
        stats.add_row(trip, getattr(trip, field), is_time)

    return stats


def biggest_trips(queryset, limit=10, disable_dist_stats=False, disable_survey_stats=False):
    stats = [
        _build_trip_stats(
            queryset=queryset,
            title="Longest trips",
            field="duration",
            metric="Duration",
            limit=limit,
            is_time=True,
        ),
    ]

    if not disable_survey_stats:
        stats += [
            _build_trip_stats(
                queryset=queryset,
                title="Surveyed",
                field="surveyed_dist",
                limit=limit,
            ),
            _build_trip_stats(
                queryset=queryset,
                title="Resurveyed",
                field="resurveyed_dist",
                limit=limit,
            ),
        ]

    if not disable_dist_stats:
        stats += [
            _build_trip_stats(
                queryset=queryset,
                title="Rope climbed",
                field="vert_dist_up",
                metric="Climbed",
                limit=limit,
            ),
            _build_trip_stats(
                queryset=queryset,
                title="Rope descended",
                field="vert_dist_down",
                metric="Descended",
                limit=limit,
            ),
            _build_trip_stats(
                queryset=queryset,
                title="Aid climbed",
                field="aid_dist",
                limit=limit,
            ),
            _build_trip_stats(
                queryset=queryset,
                title="Horizontal distance",
                field="horizontal_dist",
                metric="Distance",
                limit=limit,
            ),
        ]

    return [stat for stat in stats if stat.rows]
