from attrs import define, field
from django.utils import timezone


@define
class Statistics:
    model_name = field(type=str)
    metric = field(type=str)
    day = field(type=int)
    week = field(type=int)
    month = field(type=int)
    year = field(type=int)
    total = field(type=int)


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
