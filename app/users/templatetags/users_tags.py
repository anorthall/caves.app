from django import template

from ..models import CavingUser as User

register = template.Library()


@register.inclusion_tag("users/_user_tag.html", takes_context=True)
def user(context, user, show_username=False, link_class="link-primary"):
    if not isinstance(user, User):
        raise TypeError("user must be a Django user instance")

    return {
        "user": user,
        "show_username": show_username,
        "link_class": link_class,
    }
