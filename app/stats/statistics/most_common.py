from attrs import Factory, define, frozen
from django.db.models import Count, Sum
from logger.models import Caver


@frozen
class MostCommonRow:
    metric: str
    value: str
    url: str


@define
class MostCommonStatistics:
    title: str
    metric_name: str
    value_name: str
    rows: list = Factory(list)
    is_time: bool = False

    def add_row(self, metric, value, url=None):
        self.rows.append(MostCommonRow(metric=metric, value=value, url=url))


def _sort_comma_separated_list(qs, value, limit=10):
    """Sort a field that has a comma separated list of values from a QuerySet."""
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
        queryset.values("cave_name").annotate(count=Count("cave_name")).order_by("-count")[0:limit]
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

    results = queryset.values("type").annotate(count=Count("type")).order_by("-count")[0:limit]

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


def most_common_cavers_by_trips(queryset, limit):
    stats = MostCommonStatistics(
        title="Most common cavers by trips",
        metric_name="Caver",
        value_name="Trips",
    )

    cavers = (
        Caver.objects.filter(trip__in=queryset)
        .annotate(trip_count=Count("trip"))
        .order_by("-trip_count")[0:limit]
    )

    for caver in cavers:
        stats.add_row(caver.name, caver.trip_count, caver.get_absolute_url())

    return stats


def most_common_cavers_by_time(queryset, limit):
    stats = MostCommonStatistics(
        title="Most common cavers by time",
        metric_name="Caver",
        value_name="Time",
        is_time=True,
    )

    cavers = (
        Caver.objects.filter(trip__in=queryset)
        .annotate(duration=Sum("trip__duration"))
        .exclude(duration__isnull=True)
        .order_by("-duration")[0:limit]
    )

    for caver in cavers:
        stats.add_row(
            caver.name,
            caver.duration,
            caver.get_absolute_url(),
        )

    return stats


def most_common(queryset, limit=10):
    stats = [
        most_common_cavers_by_trips(queryset=queryset, limit=limit),
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
