from datetime import timedelta

from django import template
from django.contrib.auth import get_user_model

register = template.Library()
User = get_user_model()


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
def distformat(value, format=User.METRIC, simplify=True):
    """Format a distance object in accordance with user preferences"""
    if format == User.IMPERIAL:
        return format_imperial(value, simplify=simplify)
    else:
        return format_metric(value, simplify=simplify)


@register.filter
def get(dict, value):
    return dict[value]


@register.filter
def shortdelta(value: timedelta, simplify=True):
    """Formats a datetime as a short time string, e.g. 3d, 2w, 1y"""
    if value is None:
        return ""
    hours, remainder = divmod(value.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours)}h {int(minutes)}m"
