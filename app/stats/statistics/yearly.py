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
    earliest_year = timezone.now().year - (max_years - 1)
    total = YearlyStatistics(year=0, is_total=True)
    stats = {}

    for trip in queryset:
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
        return ()
