import os

import nh3
from django import template
from django.conf import settings
from django.utils.safestring import SafeString

from ..images import generate_imgproxy_url

register = template.Library()


@register.filter
def imgproxy(image, args=None):
    """
    Return an imgproxy URL with the given parameters

    Arguments should be separated by a comma. The following arguments
    should be given as arg=value: resizing_type, width, height, gravity,
    enlarge, extension. For example:

    width=100px,height=500px,extension=jpg

    Any further advanced arguments should be given in the format prescribed
    by the imgproxy documentation, for example:

    width=100px,height=200px,pd:10:10:10:10

    https://docs.imgproxy.net/generating_the_url

    Presets can be defined in IMGPROXY_PRESETS in the Django configuration file
    The format is as follows:

    IMGPROXY_PRESETS = {
        "preset_name": "width=100px,height=200px",
    }

    To use a preset, call this filter with the arguments "preset:name_of_preset".
    """
    if args.startswith("preset:"):
        preset_name = args.split("preset:")[1]
        try:
            args = settings.IMGPROXY_PRESETS[preset_name]
        except (AttributeError, KeyError):
            # Invalid preset, send full size image
            return generate_imgproxy_url(image.url)

    kwargs = {}
    advanced_params = ""

    args = args.split(",")
    for arg in args:
        if "=" in arg:
            k, v = arg.split("=")
            kwargs[k] = v
        else:
            advanced_params += arg

    # Rewrite URLs for local development in Docker container
    if os.environ.get("IMGPROXY_LOCAL_DEV") == "true":
        url = _rewrite_url_for_local_dev(image.url)
    else:
        url = image.url

    return generate_imgproxy_url(url, advanced_params, **kwargs)


def _rewrite_url_for_local_dev(url):
    """Rewrite URLs sent to imgproxy for local development in a Docker container"""
    # Do not rewrite S3 URLs
    if settings.AWS_S3_CUSTOM_DOMAIN in url:
        return url

    return "http://web:8000" + url


@register.filter
def clean(text: str) -> SafeString:
    """Strip HTML tags using the nh3 library"""
    return SafeString(nh3.clean(text))
