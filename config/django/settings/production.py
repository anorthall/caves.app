import os

from .base import *

# Debug should always be off in production
DEBUG = False


# Security
SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", 0))
SECURE_SSL_REDIRECT = bool(os.environ.get("SECURE_SSL_REDIRECT", 0))
SECURE_HSTS_INCLUDE_SUBDOMAINS = bool(os.environ.get("SECURE_HSTS_INCLUDE_SUBDOMAINS", 0))
SECURE_HSTS_PRELOAD = bool(os.environ.get("SECURE_HSTS_PRELOAD", 0))
SESSION_COOKIE_SECURE = bool(os.environ.get("SESSION_COOKIE_SECURE", 0))
CSRF_COOKIE_SECURE = bool(os.environ.get("CSRF_COOKIE_SECURE", 0))

# Only enable if required
if bool(os.environ.get("SECURE_PROXY_SSL_HEADER", 0)):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Logging
DEFAULT_LOG_LEVEL = "INFO"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "file": {
            "level": os.environ.get("DJANGO_LOG_LEVEL", DEFAULT_LOG_LEVEL),
            "class": "logging.FileHandler",
            "filename": "/opt/caves/logs/django/django.log",
        },
        "console": {
            "level": os.environ.get("DJANGO_LOG_LEVEL", DEFAULT_LOG_LEVEL),
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["file", "console"],
            "level": os.environ.get("DJANGO_LOG_LEVEL", DEFAULT_LOG_LEVEL),
            "propagate": True,
        },
    },
}


# Sentry integration
if os.environ.get("SENTRY_KEY", None):  # pragma: no cover
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=os.environ.get("SENTRY_KEY"),
        integrations=[
            DjangoIntegration(),
        ],
        traces_sample_rate=0.2,
        send_default_pii=True,
    )


# Google Analytics
GOOGLE_ANALYTICS_ID = os.environ.get("GOOGLE_ANALYTICS_ID", None)
if GOOGLE_ANALYTICS_ID:  # pragma: no cover
    TEMPLATES[0]["OPTIONS"]["context_processors"] += [
        "core.context_processors.google_analytics"
    ]


# Storages
STORAGES["default"] = {
    "BACKEND": "core.custom_storages.MediaS3Storage",
}

STORAGES["staticfiles"] = {
    "BACKEND": "core.custom_storages.StaticS3Storage",
}


# Media files
# MEDIA_ROOT should not be needed in production. Everything is in S3.
# MEDIA_ROOT = "/opt/caves/media/"
MEDIA_URL = os.environ.get("MEDIA_URL", "https://your.cdn.com/media/")
TEMPLATES[0]["OPTIONS"]["context_processors"] += [
    "django.template.context_processors.media"
]


# Static files (CSS, JavaScript, Images)
STATIC_ROOT = os.environ.get("STATIC_ROOT", "/opt/caves/staticfiles")
STATIC_URL = os.environ.get("STATIC_URL", "https://your.cdn.com/static/")
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
