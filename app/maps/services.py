import re
from typing import Union

import googlemaps
from django.conf import settings

LAT_LONG_REGEX_PATTERN = re.compile(
    r"^[-+]?([1-8]?\d(\.\d+)?|90(\.0+)?)"
    r",\s*[-+]?(180(\.0+)?|((1[0-7]\d)|([1-9]?\d))(\.\d+)?)$"
)


def geocode(query: str) -> tuple[str, str]:
    client = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)
    geocode_result = client.geocode(query)
    if geocode_result:
        lat, lng = geocode_result[0]["geometry"]["location"].values()
        return lat, lng
    raise ValueError("Could not geolocate query")


def split_lat_long(lat_lng: str) -> Union[tuple[str, str], tuple[None, None]]:
    if LAT_LONG_REGEX_PATTERN.match(lat_lng):
        lat = lat_lng.split(",")[0].strip()
        lng = lat_lng.split(",")[1].strip()
        return lat, lng
    return None, None
