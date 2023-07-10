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
    filesize: bool = False


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


def _add_up_fields(queryset, field):
    """
    Get the filesize of a FileField or ImageField on each object
    in a given QuerySet and return the total
    """
    total_size = 0
    for obj in queryset:
        total_size += getattr(obj, field)

    return total_size


def get_integer_field_statistics(queryset, metric, field, lookup="added__gte"):
    now = timezone.now()
    day = now - timezone.timedelta(days=1)
    week = now - timezone.timedelta(days=7)
    month = now - timezone.timedelta(days=30)
    year = now - timezone.timedelta(days=365)

    return Statistics(
        model_name=queryset.model._meta.verbose_name_plural,
        metric=metric,
        day=_add_up_fields(queryset.filter(**{lookup: day}), field),
        week=_add_up_fields(queryset.filter(**{lookup: week}), field),
        month=_add_up_fields(queryset.filter(**{lookup: month}), field),
        year=_add_up_fields(queryset.filter(**{lookup: year}), field),
        total=_add_up_fields(queryset, field),
        filesize=True,
    )
