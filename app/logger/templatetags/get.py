from django import template

register = template.Library()


@register.filter
def get(dict, value):
    return dict[value]
