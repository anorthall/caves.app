from .development import *

# Turn DEBUG on in staging
DEBUG = True

# Sessions
SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

# Storages
STORAGES["default"] = {
    "BACKEND": "core.custom_storages.MediaS3Storage",
}

# Media files
# MEDIA_ROOT should not be needed in staging or production. Everything is in S3.
MEDIA_ROOT = "/opt/dev/media/"
MEDIA_URL = env("MEDIA_URL")
TEMPLATES[0]["OPTIONS"]["context_processors"] += [
    "django.template.context_processors.media"
]

RATELIMIT_ENABLE = True

INSTALLED_APPS.remove("distancefield")
