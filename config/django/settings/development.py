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


# Storages
STORAGES["default"] = {
    "BACKEND": "django.core.files.storage.FileSystemStorage",
}

STORAGES["staticfiles"] = {
    "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
}


# Media files
MEDIA_ROOT = "/opt/dev/media/"
MEDIA_URL = "/media/"
TEMPLATES[0]["OPTIONS"]["context_processors"] += [
    "django.template.context_processors.media"
]


# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATIC_ROOT = os.environ.get("STATIC_ROOT", "/opt/caves/staticfiles")
STATICFILES_DIRS = [
    BASE_DIR / "static",
]


# Django distance field - add to INSTALLED_APPS for tests
INSTALLED_APPS += ["distancefield"]
