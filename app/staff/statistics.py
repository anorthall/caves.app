from attrs import frozen
from django.utils import timezone


@frozen
class Statistics:
    model_name: str
    metric: str
    day: int
    week: int
    month: int
    year: int
    total: int


def get_time_statistics(queryset, metric="New", lookup="added__gte"):
    now = timezone.now()
    day = now - timezone.timedelta(days=1)
    week = now - timezone.timedelta(days=7)
    month = now - timezone.timedelta(days=30)
    year = now - timezone.timedelta(days=365)

    return Statistics(
        model_name=queryset.model._meta.verbose_name_plural,
        metric=metric,
        day=queryset.filter(**{lookup: day}).count(),
        week=queryset.filter(**{lookup: week}).count(),
        month=queryset.filter(**{lookup: month}).count(),
        year=queryset.filter(**{lookup: year}).count(),
        total=queryset.count(),
    )
