import humanize
from attrs import Factory, define, frozen
from logger.models import Trip


@frozen
class TripStatsRow:
    trip: Trip
    value: str


@define
class TripStats:
    title: str
    metric: str
    rows: list = Factory(list)

    def add_row(self, trip, value):
        self.rows.append(TripStatsRow(trip=trip, value=value))


def _build_trip_stats(queryset, title, field, limit, metric=None, duration=False):
    if metric is None:
        metric = title

    stats = TripStats(title=title, metric=metric)
    qs = queryset.exclude(**{field: None}).order_by("-" + field)[:limit]

    for trip in qs:
        if duration:
            stats.add_row(
                trip,
                humanize.precisedelta(
                    getattr(trip, field),
                    minimum_unit="minutes",
                    format="%.0f",
                ),
            )
        else:
            stats.add_row(trip, getattr(trip, field))

    return stats


def biggest_trips(queryset, limit=10):
    stats = [
        _build_trip_stats(
            queryset=queryset,
            title="Longest trips",
            field="duration",
            metric="Duration",
            limit=limit,
            duration=True,
        ),
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
