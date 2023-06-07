import humanize
from django import template

register = template.Library()


@register.filter
def naturaldelta(td, min_units=None):
    if min_units is None:
        min_units = "hours"

    return humanize.precisedelta(
        td, minimum_unit=min_units, format="%.0f", suppress=["months"]
    )
