from .models import Trip


def trip_index(user):
    """Build a dict of a user's trips with their 'date index' mapped to the trip pk"""
    qs = Trip.objects.filter(user=user).order_by("start", "-pk")
    trip_list = list(qs.values_list("pk", flat=True))
    index = {}
    for trip in qs:
        index[trip.pk] = trip_list.index(trip.pk) + 1
    return index
