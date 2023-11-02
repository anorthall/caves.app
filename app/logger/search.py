from django.db.models import Q
from users.models import CavingUser

from .models import Trip

User = CavingUser


def trip_search(*, terms, for_user, search_user=None, type=None, fields=None) -> list:
    """Search through trips and return a list of results"""
    if not terms:  # pragma: no cover
        return []

    if fields is None:  # pragma: no cover
        fields = []

    # Progressively and lazily build up the query:
    # The base QuerySet will either be the user searched for, or
    # public trips + trips of the user's friends.
    if search_user:
        results = Trip.objects.filter(user=search_user)
    else:
        friends = for_user.friends.all()
        results = Trip.objects.filter(
            Q(user=for_user) | Q(user__in=friends) | Q(privacy=Trip.PUBLIC)
        )

    # Filter by trip type if provided
    if type and type.lower() != "any":
        results = results.filter(type=type)

    # Progressively add each search field with the appropriate weight
    # fields being falsey is treated as 'any field'.
    queries = _build_search_field_queries(terms, fields, for_user)
    results = results.filter(queries)

    # Prefetch related users and their friends
    results = results.select_related("user").prefetch_related("user__friends")

    # Remove trips that the user doesn't have permission to view
    sanitised_results = [
        x.sanitise(for_user) for x in results if x.is_viewable_by(for_user)
    ]

    return sanitised_results


def _build_search_field_queries(terms, fields, for_user) -> Q:
    queries = Q()
    if "cavers" in fields or not fields:
        queries |= Q(cavers__name__unaccent__icontains=terms)
    if "cave_name" in fields or not fields:
        queries |= Q(cave_name__unaccent__icontains=terms)
    if "cave_entrance" in fields or not fields:
        queries |= Q(cave_entrance__unaccent__icontains=terms)
    if "cave_exit" in fields or not fields:
        queries |= Q(cave_exit__unaccent__icontains=terms)
    if "region" in fields or not fields:
        queries |= Q(cave_region__unaccent__icontains=terms)
    if "country" in fields or not fields:
        queries |= Q(cave_country__unaccent__iexact=terms)
    if "clubs" in fields or not fields:
        queries |= Q(clubs__unaccent__icontains=terms)
    if "expedition" in fields or not fields:
        queries |= Q(expedition__unaccent__icontains=terms)
    if "notes" in fields or not fields:
        queries |= Q(
            Q(user__private_notes=False) | Q(user=for_user),
            notes__unaccent__icontains=terms,
        )

    return queries
