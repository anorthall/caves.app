import humanize
from attrs import Factory, define, frozen
from django.contrib.gis.measure import D, Distance
from django.db.models import Count
from django.utils import timezone
from logger.models import Trip


@define
class YearlyStatistics:
    year: int
    climbed: Distance = Factory(D)
    descended: Distance = Factory(D)
    surveyed: Distance = Factory(D)
    resurveyed: Distance = Factory(D)
    horizontal: Distance = Factory(D)
    aid_climbed: Distance = Factory(D)
    time: timezone.timedelta = Factory(timezone.timedelta)
    trips: int = 0
    is_total: bool = False

    def add_trip(self, trip):
        self.climbed += trip.vert_dist_up
        self.descended += trip.vert_dist_down
        self.surveyed += trip.surveyed_dist
        self.resurveyed += trip.resurveyed_dist
        self.horizontal += trip.horizontal_dist
        self.aid_climbed += trip.aid_dist
        self.time += trip.duration if trip.duration else timezone.timedelta()
        self.trips += 1


def yearly(queryset, /, max_years=10) -> tuple:
    qs = queryset.order_by("start")
    earliest_year = timezone.now().year - (max_years - 1)
    total = YearlyStatistics(year=0, is_total=True)
    stats = {}

    for trip in qs:
        # First, add to the total
        total.add_trip(trip)

        # Now, determine if we should add to the yearly stats
        year = trip.start.year
        if year < earliest_year:
            continue

        if year not in stats:
            stats[year] = YearlyStatistics(year=year)

        stats[year].add_trip(trip)

    if stats:
        # Return the stats in a tuple, with the total last
        return tuple(list(stats.values()) + [total])
    else:
        return None


@frozen
class MostCommonRow:
    metric: str
    value: str


@define
class MostCommonStatistics:
    title: str
    metric_name: str
    value_name: str
    rows: list = Factory(list)

    def add_row(self, metric, value):
        self.rows.append(MostCommonRow(metric=metric, value=value))


def _sort_comma_separated_list(qs, value, limit=10):
    """Sort a field that has a comma separated list of values from a QuerySet"""
    values = qs.values(value)
    common = {}
    for v in values:
        split_list = v[value].split(",")

        for split_value in split_list:
            trimmed = split_value.strip()

            if not trimmed:
                continue

            if trimmed in common:
                common[trimmed] += 1
            else:
                common[trimmed] = 1

    return sorted(common.items(), key=lambda x: x[1], reverse=True)[0:limit]


def most_common_caves(queryset, limit):
    stats = MostCommonStatistics(
        title="Most common caves",
        metric_name="Cave",
        value_name="Trips",
    )

    results = (
        queryset.values("cave_name")
        .annotate(count=Count("cave_name"))
        .order_by("-count")[0:limit]
    )

    for result in results:
        stats.add_row(result["cave_name"], result["count"])

    return stats


def most_common_trip_types(queryset, limit):
    stats = MostCommonStatistics(
        title="Most common trip types",
        metric_name="Trip type",
        value_name="Trips",
    )

    results = (
        queryset.values("type")
        .annotate(count=Count("type"))
        .order_by("-count")[0:limit]
    )

    for result in results:
        stats.add_row(result["type"], result["count"])

    return stats


def most_common_from_csv(*, queryset, field, title, metric_name, value_name, limit):
    stats = MostCommonStatistics(
        title=title,
        metric_name=metric_name,
        value_name=value_name,
    )

    results = _sort_comma_separated_list(queryset, field, limit=limit)

    for result in results:
        stats.add_row(result[0], result[1])

    return stats


def most_common_cavers_by_time(queryset, limit):
    stats = MostCommonStatistics(
        title="Most common cavers by time",
        metric_name="Caver",
        value_name="Time",
    )

    cavers = {}
    for trip in queryset:
        if not trip.cavers:
            continue

        for caver in trip.cavers.split(","):
            caver = caver.strip()
            if not caver:
                continue

            if caver not in cavers:
                cavers[caver] = timezone.timedelta()

            cavers[caver] += trip.duration if trip.duration else timezone.timedelta()

    results = sorted(cavers.items(), key=lambda x: x[1], reverse=True)[0:limit]

    for row in results:
        stats.add_row(
            row[0],
            humanize.precisedelta(row[1], minimum_unit="minutes", format="%.0f"),
        )

    return stats


def most_common(queryset, limit=10):
    stats = [
        most_common_from_csv(
            queryset=queryset,
            field="cavers",
            title="Most common cavers by trips",
            metric_name="Caver",
            value_name="Trips",
            limit=limit,
        ),
        most_common_cavers_by_time(queryset, limit),
        most_common_caves(queryset, limit),
        most_common_from_csv(
            queryset=queryset,
            field="clubs",
            title="Most common clubs",
            metric_name="Club",
            value_name="Trips",
            limit=limit,
        ),
        most_common_trip_types(queryset, limit),
    ]

    return [stat for stat in stats if stat.rows]


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
