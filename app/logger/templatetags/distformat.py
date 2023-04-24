from django import template
from users.models import UserSettings

register = template.Library()


def format_imperial(value, simplify=True):
    """Format a distance object in feet and miles"""
    feet = round(value.ft)
    if simplify:
        if feet > 99999:
            miles = round(value.mi, 2)
            return f"{miles}mi"
    return f"{feet}ft"


def format_metric(value, simplify=True):
    """Format a distance object in metric units"""
    metres = round(value.m)
    if simplify:
        if metres > 99999:
            km = round(value.km, 2)
            return f"{km}km"
    return f"{metres}m"


@register.filter
def distformat(value, format=UserSettings.METRIC, simplify=True):
    """Format a distance object in accordance with user preferences"""
    if format == UserSettings.IMPERIAL:
        return format_imperial(value, simplify=simplify)
    else:
        return format_metric(value, simplify=simplify)
