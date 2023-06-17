"""
Module to handle generation of imgproxy URLs using the imgproxy
python library

https://pypi.org/project/imgproxy/
"""

from imgproxy import ImgProxy
from django.conf import settings


def get_imgproxy():
    return ImgProxy.factory(
        proxy_host=settings.IMGPROXY_URL,
        key=settings.IMGPROXY_KEY,
        salt=settings.IMGPROXY_SALT,
    )


def generate_imgproxy_url(*args, **kwargs):
    return get_imgproxy()(*args, **kwargs)
