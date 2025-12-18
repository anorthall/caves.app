import socket

from .base import *  # noqa: F403
from .base import INSTALLED_APPS, MIDDLEWARE

DEBUG = True
RATELIMIT_ENABLE = False
INSTALLED_APPS += ["debug_toolbar", "django_browser_reload"]
MIDDLEWARE += [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django_browser_reload.middleware.BrowserReloadMiddleware",
]

# Find local IPs for debug toolbar
try:
    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS = [ip[: ip.rfind(".")] + ".1" for ip in ips] + [
        "127.0.0.1",
        "10.0.2.2",
        "192.168.65.1",
    ]
except socket.gaierror:
    INTERNAL_IPS = ["127.0.0.1", "10.0.2.2", "192.168.65.1"]

INSTALLED_APPS += ["distancefield"]
