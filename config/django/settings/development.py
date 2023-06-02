import socket

from .base import *

# Debug
DEBUG = True


# Django debug toolbar
INSTALLED_APPS += ["debug_toolbar"]
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]

# Find local IPs for debug toolbar
hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
INTERNAL_IPS = [ip[: ip.rfind(".")] + ".1" for ip in ips] + [
    "127.0.0.1",
    "10.0.2.2",
]

# Media files
MEDIA_ROOT = "/opt/dev/media/"
MEDIA_URL = "/media/"
TEMPLATES[0]["OPTIONS"]["context_processors"] += [
    "django.template.context_processors.media"
]
