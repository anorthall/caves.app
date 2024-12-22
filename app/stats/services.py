from django.core.exceptions import PermissionDenied
from django.http import Http404
from users.models import CavingUser as User


def use_units(value, units):
    """Return the value in the required units, based on the user's preferred units."""
    if units == User.IMPERIAL:
        return value.ft
    return value.m


def match_and_check_username(request, username):
    """Match a username to a user, and check the request user equals that user."""
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return Http404

    if not request.user == user:
        raise PermissionDenied

    return user
