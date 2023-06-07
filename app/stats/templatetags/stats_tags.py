import humanize
from django import template

register = template.Library()


@register.filter
def naturaldelta(td, simplify=True):
    return humanize.precisedelta(
        td, minimum_unit="hours", format="%.0f", suppress=["months"]
    )
