import os
from copy import deepcopy
from pathlib import Path
from typing import TypedDict

import environ
from django.contrib.messages import constants as messages

env = environ.Env()

# BASE_DIR should point to where manage.py is
SETTINGS_DIR = Path(__file__).resolve().parent
DJANGO_ROOT = SETTINGS_DIR.parent.parent / "app"

DATETIME_FORMAT = "H:i Y-m-d"
DATE_FORMAT = "Y-m-d"
TIME_FORMAT = "H:i"

SITE_ROOT = env("SITE_ROOT", str, "http://127.0.0.1:8000")
SITE_TITLE = env("SITE_TITLE", str, "devel.app")
ADMIN_URL = env("ADMIN_URL", str, "admin/")
STAFF_URL = env("STAFF_URL", str, "staff/")

IMGPROXY_URL = env("IMGPROXY_URL", str, "http://127.0.0.1:9000/imgproxy")
IMGPROXY_KEY = env("IMGPROXY_KEY", str, "")
IMGPROXY_SALT = env("IMGPROXY_SALT", str, "")
IMGPROXY_PRESETS = {
    "photo": "width=1000,height=1000,resizing_type=fit",
    "tripphoto_thumb": "width=400,height=600,resizing_type=fill",
    "avatar": "width=400,height=400,resizing_type=fill",
    "avatar_navbar": "width=80,height=80,resizing_type=fill",
    "featured_photo": "width=1800,height=800,resizing_type=fill-down",
}

SECRET_KEY = env("SECRET_KEY", str, "insecure-secret-key")
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS", str, "http://127.0.0.1").split(" ")
CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS", str, "http://127.0.0.1").split(" ")

# Need this many for CSV import feature to work - 16 fields per trip
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10_000

# Email settings
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", str, "admin@yourapp.com")
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
MAILER_EMAIL_BACKEND = env("MAILER_EMAIL_BACKEND", cast=str, default=EMAIL_BACKEND)
MAILER_EMPTY_QUEUE_SLEEP = 10

EMAIL_HOST = env("EMAIL_HOST", str, "")
EMAIL_PORT = env("EMAIL_PORT", int, 0)
EMAIL_USE_SSL = env("EMAIL_USE_SSL", bool, False)
EMAIL_USE_TLS = env("EMAIL_USE_TLS", bool, False)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", str, "")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", str, "")

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = False
USE_TZ = True

INSTALLED_APPS = [
    "whitenoise.runserver_nostatic",
    "core.apps.CoreConfig",
    "users.apps.UsersConfig",
    "logger.apps.LoggerConfig",
    "staff.apps.StaffConfig",
    "stats.apps.StatsConfig",
    "data_import.apps.ImportConfig",
    "data_export.apps.ExportConfig",
    "comments.apps.CommentsConfig",
    "maps.apps.MapsConfig",
    "dal",
    "dal_select2",
    "django_countries",
    "active_link",
    "mailer",
    "crispy_forms",
    "crispy_bootstrap5",
    "django_htmx",
    "markdownify",
    "unfold",
    "django_rich",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django.contrib.postgres",
    "django.contrib.gis",
]

LOGIN_URL = "users:login"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
AUTH_USER_MODEL = "users.CavingUser"

MESSAGE_TAGS = {
    messages.DEBUG: "alert-secondary",
    messages.INFO: "alert-info",
    messages.SUCCESS: "alert-success",
    messages.WARNING: "alert-warning",
    messages.ERROR: "alert-danger",
}

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "users.middleware.TimezoneMiddleware",
    "users.middleware.LastSeenMiddleware",
    "users.middleware.DistanceUnitsMiddleware",
    "users.middleware.NotificationsMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [DJANGO_ROOT / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.media",
                "users.context_processors.notifications",
                "core.context_processors.site_root",
                "core.context_processors.site_title",
                "core.context_processors.api_keys",
            ],
        },
    },
]

WSGI_APPLICATION = "conf.django.wsgi.application"
ROOT_URLCONF = "conf.urls"

CACHES = {
    "default": env.cache(
        var="REDIS_URL",
        default="redis://redis:6379/0",
        backend="django.core.cache.backends.redis.RedisCache",
    ),
}

DATABASES = {
    "default": env.db(
        var="DATABASE_URL",
        default="postgres://postgres:postgres@postgres:5432/postgres",
        engine="django.contrib.gis.db.backends.postgis",
    )
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Static files, media files, and Amazon S3.
# Photos are *always* stored in S3, even in development.
AWS_S3_DEFAULT_ACL = env("AWS_S3_DEFAULT_ACL", str, "private")
AWS_S3_PRESIGNED_EXPIRY = env("AWS_S3_PRESIGNED_EXPIRY", int, 600)
AWS_S3_CUSTOM_DOMAIN = env("AWS_S3_CUSTOM_DOMAIN", str, "")
AWS_S3_ACCESS_KEY_ID = env("AWS_S3_ACCESS_KEY_ID", str, "")
AWS_S3_SECRET_ACCESS_KEY = env("AWS_S3_SECRET_ACCESS_KEY", str, "")
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME", str, "")
AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", str, "")

STATIC_URL = "/static/"
STATIC_ROOT = "/app/staticfiles"
STATICFILES_DIRS = [DJANGO_ROOT / "static"]

MEDIA_STORAGE_LOCATION = "m"
PHOTOS_STORAGE_LOCATION = "p"

MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/" if AWS_S3_CUSTOM_DOMAIN else "/media/"
MEDIA_ROOT = "/app/mediafiles"

_MEDIA_DEFAULT_BACKEND = (
    "storages.backends.s3.S3Storage"
    if AWS_S3_CUSTOM_DOMAIN
    else "django.core.files.storage.FileSystemStorage"
)

STORAGES = {
    "default": {
        "BACKEND": _MEDIA_DEFAULT_BACKEND,
        "OPTIONS": {"location": "m"},
    },
    "photos": {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {"location": "p"},
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}


class _MarkdownifyConfig(TypedDict):
    WHITELIST_TAGS: list[str]
    WHITELIST_STYLES: list[str]
    MARKDOWN_EXTENSIONS: list[str]
    LINKIFY_TEXT: dict[str, bool]


_MARKDOWNIFY_DEFAULT: _MarkdownifyConfig = {
    "WHITELIST_TAGS": [
        "a",
        "abbr",
        "acronym",
        "b",
        "blockquote",
        "em",
        "i",
        "li",
        "ol",
        "p",
        "strong",
        "ul",
        "code",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "h7",
    ],
    "WHITELIST_STYLES": [
        "color",
        "font-weight",
    ],
    "MARKDOWN_EXTENSIONS": [
        "fenced_code",
    ],
    "LINKIFY_TEXT": {
        "PARSE_URLS": True,
    },
}

MARKDOWNIFY = {
    "default": deepcopy(_MARKDOWNIFY_DEFAULT),
    "news": deepcopy(_MARKDOWNIFY_DEFAULT),
    "plain": {
        "WHITELIST_TAGS": ["p", "a", "strong", "blockquote", "em", "i", "b"],
        "LINKIFY_TEXT": {"PARSE_URLS": True},
    },
}

MARKDOWNIFY["news"]["WHITELIST_TAGS"].append("img")
MARKDOWNIFY["news"]["WHITELIST_ATTRS"] = ["src", "alt", "title", "class", "href"]

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

ACTIVE_LINK_STRICT = True

DEFAULT_LOG_LEVEL = env("DJANGO_LOG_LEVEL", str, "ERROR")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "[{levelname}] [{asctime}] {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": DEFAULT_LOG_LEVEL,
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": DEFAULT_LOG_LEVEL,
            "propagate": True,
        },
        "user_actions": {
            "handlers": ["console"],
            "level": "INFO",
        },
    },
}

GOOGLE_MAPS_PRIVATE_API_KEY = env("GOOGLE_MAPS_PRIVATE_API_KEY", str, "")
GOOGLE_MAPS_PUBLIC_API_KEY = env("GOOGLE_MAPS_PUBLIC_API_KEY", str, "")
GOOGLE_MAPS_USER_MAP_ID = env("GOOGLE_MAPS_USER_MAP_ID", str, "")

if os.getenv("GDAL_LIBRARY_PATH"):  # pragma: no cover
    GDAL_LIBRARY_PATH = env("GDAL_LIBRARY_PATH", str, "")

if os.getenv("GEOS_LIBRARY_PATH"):  # pragma: no cover
    GEOS_LIBRARY_PATH = env("GEOS_LIBRARY_PATH", str, "")

TEST_RUNNER = "django_rich.test.RichRunner"
