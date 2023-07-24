import logging

from users.models import CavingUser
from logger.models import Trip, TripReport, TripPhoto


ActionLogger = logging.getLogger("user_actions")


def _log_action(user: CavingUser, message: str):
    user = _format_user_for_logging(user)
    ActionLogger.info(f"{user} {message}")


def _format_user_for_logging(user: CavingUser) -> str:
    return f"{user.name} ({user.pk}) <{user.email}>"


def _format_trip_for_logging(trip: Trip) -> str:
    start = trip.start.strftime("%Y-%m-%d")
    if trip.pk:
        pk = f" ({trip.pk})"
    else:
        pk = ""

    return f'"{trip.cave_name}" on {start}{pk}'


def log_trip_action(user: CavingUser, trip: Trip, verb: str, extra: str = ""):
    trip = _format_trip_for_logging(trip)
    if extra:
        extra = f": ({extra})"

    _log_action(user, f"{verb} a trip to {trip}{extra}")


def log_tripreport_action(
        user: CavingUser, report: TripReport, verb: str, extra: str = ""
):
    trip = _format_trip_for_logging(report.trip)
    if extra:
        extra = f": ({extra})"

    _log_action(user, f"{verb} a trip report for the trip to {trip}{extra}")


def log_tripphoto_action(
        user: CavingUser, photo: TripPhoto, verb: str, extra: str = ""
):
    trip = _format_trip_for_logging(photo.trip)
    if extra:
        extra = f": ({extra})"

    _log_action(user, f"{verb} a photo for the trip to {trip}{extra}")


def log_user_action(user: CavingUser, message: str):
    _log_action(user, message)


def log_user_interaction(user1: CavingUser, action: str, user2: CavingUser):
    user2 = _format_user_for_logging(user2)
    _log_action(user1, f"{action} {user2}")
