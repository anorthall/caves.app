from django.db.models import Q

from .models import Trip


def trip_search(*, terms, for_user, search_user=None, limit=500):
    """Search through trips and return a list of results"""
    if not terms:
        return Trip.objects.none()

    if search_user:
        results = Trip.objects.filter(user=search_user)
    else:
        friends = for_user.friends.all()
        results = Trip.objects.filter(
            Q(user=for_user) | Q(user__in=friends) | Q(privacy=Trip.PUBLIC)
        )

    results = results.filter(
        Q(cave_name__unaccent__trigram_similar=terms)
        | Q(cave_region__unaccent__icontains=terms)  # noqa W504
        | Q(cave_country__unaccent__iexact=terms)  # noqa W504
    )[:limit]

    results = results.select_related("user").prefetch_related("user__friends")

    # Remove trips that the user doesn't have permission to view
    sanitised_results = [x for x in results if x.is_viewable_by(for_user)]
    return sanitised_results
