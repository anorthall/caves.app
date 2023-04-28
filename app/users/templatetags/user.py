from django import template
from django.contrib.auth import get_user_model

register = template.Library()
User = get_user_model()


@register.inclusion_tag("includes/user_tag.html", takes_context=True)
def user(context, user, show_username=False):
    if not isinstance(user, User):
        raise TypeError("user must be a Django user instance")

    return {
        "user": user,
        "show_username": show_username,
        "show_profile_link": user.is_viewable_by(context["request"].user),
    }
