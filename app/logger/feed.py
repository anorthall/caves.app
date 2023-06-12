from django.contrib.auth import get_user_model
from django.core.paginator import EmptyPage, Paginator
from django.db.models import Count, Exists, OuterRef, Q

from .models import Trip

User = get_user_model()


def get_trips_context(request, ordering, page=1):
    """Return a paginated list of trips that the user has permission to view"""
    friends = request.user.friends.all()

    trips = (
        Trip.objects.filter(Q(user__in=friends) | Q(user=request.user))
        .select_related("user")
        .prefetch_related("photos", "likes", "user__friends")
        .annotate(
            likes_count=Count("likes", distinct=True),
            user_liked=Exists(
                User.objects.filter(
                    pk=request.user.pk, liked_trips=OuterRef("pk")
                ).only("pk")
            ),
        )
    ).order_by(ordering)[:100]

    # Remove trips that the user does not have permission to view.
    sanitised_trips = [x for x in trips if x.is_viewable_by(request.user)]

    try:
        paginated_trips = Paginator(
            object_list=sanitised_trips, per_page=10, allow_empty_first_page=False
        ).page(page)
    except EmptyPage:
        return []

    return paginated_trips


def get_liked_str_context(request, trips):
    """Return a dictionary of liked strings for each trip
    This dictionary will be used in the includes/htmx_trip_like.html template
    """
    friends = request.user.friends.all()
    liked_str_index = {}
    for trip in trips:
        liked_str_index[trip.pk] = trip.get_liked_str(request.user, friends)

    return liked_str_index
