from attrs import frozen
from django.db.models import Count
from django.db.models.functions import Lower, Trim


@frozen
class Row:
    metric: str
    value: str | int


def metrics(queryset):
    rows = [
        Row(metric="Unique caves entered", value=unique_caves(queryset)),
        Row(metric="Unique entrances/exits used", value=unique_entrance_exit(queryset)),
        Row(metric="Unique countries", value=unique_countries(queryset)),
        Row(metric="Unique regions", value=unique_regions(queryset)),
        Row(metric="Cavers caved with", value=unique_cavers(queryset)),
    ]

    # Clear out any rows with a zero value
    return [row for row in rows if row.value]


def unique_caves(queryset):
    return queryset.values(cave=Lower("cave_name")).distinct().count()


def unique_entrance_exit(queryset):
    uniques = set()
    for trip in queryset:
        if trip.cave_entrance or trip.cave_exit:
            if trip.cave_entrance:
                uniques.add(trip.cave_entrance)
            if trip.cave_exit:
                uniques.add(trip.cave_exit)
        else:
            uniques.add(trip.cave_name)

    return len(uniques)


def unique_countries(queryset):
    return queryset.values(country=Trim(Lower("cave_country"))).distinct().count()


def unique_regions(queryset):
    return queryset.values(region=Trim(Lower("cave_region"))).distinct().count()


def unique_cavers(queryset):
    return queryset.aggregate(cavers=Count("cavers", distinct=True))["cavers"]
