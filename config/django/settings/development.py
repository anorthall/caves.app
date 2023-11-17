import socket

from .base import *

# Debug
DEBUG = True

# Testing
TEST_RUNNER = "django_rich.test.RichRunner"

# Django debug toolbar
INSTALLED_APPS += ["debug_toolbar"]
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]

# Find local IPs for debug toolbar
hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
INTERNAL_IPS = [ip[: ip.rfind(".")] + ".1" for ip in ips] + [
    "127.0.0.1",
    "10.0.2.2",
    "192.168.65.1",
]

# Django distance field - add to INSTALLED_APPS for tests
INSTALLED_APPS += ["distancefield"]

# Disable rate limiting
RATELIMIT_ENABLE = False
