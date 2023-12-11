from datetime import datetime

from attrs import Factory, define
from django.contrib.gis.measure import D, Distance
from django.utils import timezone


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
    dates: list[datetime.date] = Factory(list)
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

        # Collect a list of dates that this trip spans. The start date is always added,
        # and then if the trip is over 24 hours, we add one additional date for each
        # 24 hour period. datetime.timedelta.days returns 0 for timedeltas less than
        # so the loop will not run for trips less than 24 hours.

        self.dates.append(trip.start.date())
        if trip.duration:
            for i in range(1, trip.duration.days + 1):
                self.dates.append((trip.start + timezone.timedelta(days=i)).date())

    @property
    def caving_days(self):
        return len(set(self.dates))

    @property
    def caving_hours(self):
        return self.time.total_seconds() / 60 / 60


def yearly(queryset, /, max_years=10) -> tuple:
    earliest_year = timezone.now().year - (max_years - 1)
    total = YearlyStatistics(year=0, is_total=True)
    stats = {}

    for trip in queryset:
        # First, add to the total
        total.add_trip(trip)

        # Now, determine if we should add to the yearly stats
        year = trip.start.year
        if year < earliest_year:  # pragma: no cover
            continue

        if year not in stats:
            stats[year] = YearlyStatistics(year=year)

        stats[year].add_trip(trip)

    if not stats:
        return ()
    stats = list(stats.values())
    return tuple(sorted(stats, key=lambda s: s.year, reverse=True) + [total])
