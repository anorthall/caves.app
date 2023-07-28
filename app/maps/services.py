import datetime
import re
from typing import Union

import googlemaps
from attrs import frozen
from django.conf import settings
from users.models import CavingUser


LAT_LONG_REGEX_PATTERN = re.compile(
    r"^[-+]?([1-8]?\d(\.\d+)?|90(\.0+)?)"
    r",\s*[-+]?(180(\.0+)?|((1[0-7]\d)|([1-9]?\d))(\.\d+)?)$"
)


def geocode(query: str) -> tuple[float, float]:
    client = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)
    geocode_result = client.geocode(query)
    if geocode_result:
        lat, lng = geocode_result[0]["geometry"]["location"].values()
        return lat, lng
    raise ValueError("Could not geolocate query")


def split_lat_long(lat_lng: str) -> Union[tuple[float, float]]:
    if LAT_LONG_REGEX_PATTERN.match(lat_lng):
        lat = lat_lng.split(",")[0].strip()
        lng = lat_lng.split(",")[1].strip()
        return float(lat), float(lng)
    raise ValueError("String is not a valid lat and long")


def get_lat_long_from(lat_lng: str) -> tuple[float, float]:
    try:
        return split_lat_long(lat_lng)
    except ValueError:
        return geocode(lat_lng)

@frozen
class Marker:
    lat: float
    lng: float
    title: str
    visits: int
    last_visit: datetime.date
    last_trip_url: str


def get_markers_for_user(user: CavingUser) -> list[Marker]:
    trips = user.trips.filter(cave_coordinates__isnull=False)
    if not trips:
        return []

    # Create a dict of coordinates to count visits to a specific location.
    # visits["lat,lng"] = [
    #     name_of_cave: str,
    #     lat: float,
    #     lng: float,
    #     visits: int,
    #     last_visit: datetime.date,
    #     last_trip_url: str
    # ]
    visits = {}
    for trip in trips:
        coords = f"{trip.latitude},{trip.longitude}"
        if coords in visits:
            visits[coords][3] += 1
            if trip.start.date() > visits[coords][4]:
                visits[coords][4] = trip.start.date()
                visits[coords][5] = trip.get_absolute_url()
            continue

        name = trip.cave_entrance or trip.cave_name
        visits[coords] = [
            name,
            trip.latitude,
            trip.longitude,
            1,
            trip.start.date(),
            trip.get_absolute_url(),
        ]

    markers = []
    for key, data in visits.items():
        name, lat, lng, visits, last_visit, last_trip_url = data
        markers.append(
            Marker(
                lat=lat,
                lng=lng,
                title=name,
                visits=visits,
                last_visit=last_visit,
                last_trip_url=last_trip_url,
            )
        )

    return markers
