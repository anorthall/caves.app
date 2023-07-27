import re
from typing import Union

import googlemaps
from django.conf import settings

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
