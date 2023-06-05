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


def get_time_statistics(model, metric="New", lookup="added__gte"):
    """Get time-based statistics for a model"""
    now = timezone.now()
    day = now - timezone.timedelta(days=1)
    week = now - timezone.timedelta(days=7)
    month = now - timezone.timedelta(days=30)
    year = now - timezone.timedelta(days=365)

    return Statistics(
        model_name=model._meta.verbose_name_plural,
        metric=metric,
        day=model.objects.filter(**{lookup: day}).count(),
        week=model.objects.filter(**{lookup: week}).count(),
        month=model.objects.filter(**{lookup: month}).count(),
        year=model.objects.filter(**{lookup: year}).count(),
        total=model.objects.count(),
    )
