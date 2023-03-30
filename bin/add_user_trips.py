#!/usr/bin/env python
# Copy to app/ to run!
from pathlib import Path

TRIP_FILE = "file.csv"
USER_EMAIL = "user@email.address"
DOTENV = "etc/dev/dev.env"
APP_NAME = "cavinglog.settings"
DRY_RUN = True
TIMEZONE = "Europe/London"
UNITS = "m"

#####################
# End of user input #
#####################

BASE_DIR = Path(__file__).resolve().parent

import django, csv, os, humanize
from django.contrib.gis.measure import D
from django.contrib.auth import get_user_model
from django.utils import timezone
from dotenv import load_dotenv
from zoneinfo import ZoneInfo

os.environ.setdefault("DJANGO_SETTINGS_MODULE", APP_NAME)
load_dotenv(os.path.join(BASE_DIR, DOTENV))
django.setup()


def convert_date(date, time):
    """Convert date and time to datetime"""
    year, month, day = date.split("-")
    hour, minute = time.split(":")
    return timezone.datetime(
        year=int(year),
        month=int(month),
        day=int(day),
        hour=int(hour),
        minute=int(minute),
        tzinfo=ZoneInfo(TIMEZONE),
    )


def convert_dist(dist):
    """Add units to distance"""
    if not dist:
        return "0m"
    return f"{dist}{UNITS}"


from logger.models import Trip

user = get_user_model().objects.get(email=USER_EMAIL)
with open(os.path.join(BASE_DIR, TRIP_FILE)) as f:
    r = csv.reader(f)
    next(r)  # Skip header
    # 0: Start Date, 1: Start Time, 2: End Date, 3: End Time, 4: Duration, 5: Cave Name
    # 6: Cave Region, 7: Cave Country, 8: Type, 9: Cavers, 10: Vert Dist Up, 11: Vert Dist Down,
    # 12: Surveyed, 13: Resurveyed, 14: Aided, 15: Notes

    # Stats
    x = 0
    total_dur = timezone.timedelta(0)
    total_v_up = D(m=0)
    total_v_down = D(m=0)
    total_surveyed = D(m=0)
    total_resurveyed = D(m=0)
    survey_total = D(m=0)
    total_aided = D(m=0)

    for row in r:
        x += 1
        (
            s_date,
            s_time,
            e_date,
            e_time,
            duration,
            c_name,
            c_region,
            c_country,
            trip_type,
            cavers,
            v_up,
            v_down,
            surveyed,
            resurveyed,
            aided,
            notes,
        ) = row

        # Convert dates and times to datetime
        start_dt = convert_date(s_date, s_time)
        end_dt = convert_date(e_date, e_time)

        new_trip = Trip.objects.create(
            user=user,
            start=start_dt,
            end=end_dt,
            cave_name=c_name,
            cave_region=c_region,
            cave_country=c_country,
            type=trip_type,
            cavers=cavers,
            vert_dist_up=convert_dist(v_up),
            vert_dist_down=convert_dist(v_down),
            surveyed_dist=convert_dist(surveyed),
            resurveyed_dist=convert_dist(resurveyed),
            aid_dist=convert_dist(aided),
            notes=notes,
        )

        total_dur += new_trip.duration
        total_v_up += new_trip.vert_dist_up
        total_v_down += new_trip.vert_dist_down
        total_surveyed += new_trip.surveyed_dist
        total_resurveyed += new_trip.resurveyed_dist
        survey_total += new_trip.surveyed_dist + new_trip.resurveyed_dist
        total_aided += new_trip.aid_dist

        print(
            f"Created new trip #{x} to {new_trip.cave_name} on {new_trip.start} to {new_trip.end}. Duration: {new_trip.duration_str}."
        )
        if DRY_RUN:
            new_trip.delete()

    print("\n")

    if DRY_RUN:
        print("Dry run complete. No trips were added.\n\n")

    print("Statistics of added trips:")
    print(f"Trips added: {x}")
    print(f"Total duration: {humanize.precisedelta(total_dur)}")
    print(f"Total hours: {total_dur.total_seconds() / 3600:.2f}\n")

    print(f"Total vertical distance up:")
    print(f"      ft: {total_v_up.ft:.2f}")
    print(f"      m: {total_v_up.m:.2f}")
    print(f"      mi: {total_v_up.mi:.2f}")
    print(f"      km: {total_v_up.km:.2f}")

    print(f"Total vertical distance down:")
    print(f"      ft: {total_v_down.ft:.2f}")
    print(f"      m: {total_v_down.m:.2f}")
    print(f"      mi: {total_v_down.mi:.2f}")
    print(f"      km: {total_v_down.km:.2f}")

    print(f"Total surveyed distance:")
    print(f"      ft: {total_surveyed.ft:.2f}")
    print(f"      m: {total_surveyed.m:.2f}")
    print(f"      mi: {total_surveyed.mi:.2f}")
    print(f"      km: {total_surveyed.km:.2f}")

    print("Total resurveyed distance:")
    print(f"      ft: {total_resurveyed.ft:.2f}")
    print(f"      m: {total_resurveyed.m:.2f}")
    print(f"      mi: {total_resurveyed.mi:.2f}")
    print(f"      km: {total_resurveyed.km:.2f}")

    print(f"Total surveyed and resurveyed distance:")
    print(f"      ft: {survey_total.ft:.2f}")
    print(f"      m: {survey_total.m:.2f}")
    print(f"      mi: {survey_total.mi:.2f}")
    print(f"      km: {survey_total.km:.2f}")

    print(f"Total aided distance:")
    print(f"      ft: {total_aided.ft:.2f}")
    print(f"      m: {total_aided.m:.2f}")
    print(f"      mi: {total_aided.mi:.2f}")
    print(f"      km: {total_aided.km:.2f}")
