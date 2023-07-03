from .base import *

# Debug should always be off in production
DEBUG = False


# Security
SECURE_HSTS_SECONDS = env("SECURE_HSTS_SECONDS", 0, int)
SECURE_SSL_REDIRECT = env("SECURE_SSL_REDIRECT", False, bool)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env("SECURE_HSTS_INCLUDE_SUBDOMAINS", False, bool)
SECURE_HSTS_PRELOAD = env("SECURE_HSTS_PRELOAD", False, bool)
SESSION_COOKIE_SECURE = env("SESSION_COOKIE_SECURE", False, bool)
CSRF_COOKIE_SECURE = env("CSRF_COOKIE_SECURE", False, bool)

# Only enable if required
if env("SECURE_PROXY_SSL_HEADER", False, bool):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Logging
DEFAULT_LOG_LEVEL = "INFO"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "file": {
            "level": env("DJANGO_LOG_LEVEL", DEFAULT_LOG_LEVEL),
            "class": "logging.FileHandler",
            "filename": "/opt/caves/logs/django/django.log",
        },
        "console": {
            "level": env("DJANGO_LOG_LEVEL", DEFAULT_LOG_LEVEL),
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["file", "console"],
            "level": env("DJANGO_LOG_LEVEL", DEFAULT_LOG_LEVEL),
            "propagate": True,
        },
    },
}


# Sentry integration
if env("SENTRY_KEY", ""):  # pragma: no cover
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=env("SENTRY_KEY"),
        integrations=[
            DjangoIntegration(),
        ],
        traces_sample_rate=0.2,
        send_default_pii=True,
    )


# Google Analytics
GOOGLE_ANALYTICS_ID = env("GOOGLE_ANALYTICS_ID", "")
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
MEDIA_URL = env("MEDIA_URL")
TEMPLATES[0]["OPTIONS"]["context_processors"] += [
    "django.template.context_processors.media"
]


# Static files (CSS, JavaScript, Images)
STATIC_ROOT = env("STATIC_ROOT", "/opt/caves/staticfiles")
STATIC_URL = env("STATIC_URL")
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
