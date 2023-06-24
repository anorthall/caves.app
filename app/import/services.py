from datetime import datetime
from typing import Union

from dateutil import parser
from logger.models import Trip

FIELD_MAP = (
    ("cave_name", "Cave name"),
    ("cave_entrance", "Cave entrance"),
    ("cave_exit", "Cave exit"),
    ("cave_region", "Cave region"),
    ("cave_country", "Cave country"),
    ("cave_url", "Cave website"),
    ("start", "Start date/time"),
    ("end", "End date/time"),
    ("type", "Type"),
    ("privacy", "Privacy"),
    ("clubs", "Clubs"),
    ("expedition", "Expedition"),
    ("cavers", "Cavers"),
    ("horizontal_dist", "Horizontal dist"),
    ("vert_dist_down", "Vertical dist down"),
    ("vert_dist_up", "Vertical dist up"),
    ("surveyed_dist", "Surveyed dist"),
    ("resurveyed_dist", "Resurveyed dist"),
    ("aid_dist", "Aid dist"),
    ("notes", "Notes"),
)


def generate_sample_csv():
    return ",".join([x[1] for x in FIELD_MAP])


def get_headers():
    return [x[0] for x in FIELD_MAP]


def get_formset_with_data(rows, data_only=False):
    """Transform the rows into formset data to allow validation on data upload"""
    from .forms import TripImportFormset  # Avoid circular import

    data = {
        "form-TOTAL_FORMS": len(rows),
        "form-INITIAL_FORMS": 0,
    }
    for i, row in enumerate(rows):
        row = clean_row(row)
        for key, value in row.items():
            data[f"form-{i}-{key}"] = value

    if data_only:
        return data
    return TripImportFormset(data)


def clean_row(row):
    """Reformat the row data to be compatible with the formset"""
    cleaned_row = {}
    for key, value in row.items():
        if value:
            cleaned_row[key] = str(value).strip()
        else:
            cleaned_row[key] = ""

    cleaned_row["start"] = clean_datetime(cleaned_row["start"])
    cleaned_row["end"] = clean_datetime(cleaned_row["end"])
    cleaned_row["privacy"] = clean_privacy(cleaned_row["privacy"])
    cleaned_row["type"] = clean_type(cleaned_row["type"])
    return cleaned_row


def clean_privacy(privacy: str) -> str:
    if not privacy:
        return Trip.DEFAULT
    return privacy


def clean_type(trip_type: str) -> str:
    return trip_type.capitalize()


def clean_datetime(time: str) -> Union[datetime, None]:
    try:
        return parser.parse(time, ignoretz=True)
    except parser.ParserError:
        return None


def get_trip_types() -> str:
    """Return a human readable comma separated list of valid trip types"""
    initial = ", ".join([x[1].lower() for x in Trip.TRIP_TYPES[:-1]])
    return f"{initial} and {Trip.TRIP_TYPES[-1][1].lower()}"
