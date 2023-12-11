import copy
import os
import socket
from pathlib import Path
from typing import Any

import dj_database_url
from django.contrib.messages import constants as messages
from django.core.exceptions import ImproperlyConfigured


def env(name, default=None, force_type: Any = str):
    setting = os.environ.get(name, default)
    if setting is None:
        raise ImproperlyConfigured(f"{name} environment variable is not set")

    try:
        return force_type(setting)
    except ValueError:
        raise ImproperlyConfigured(
            f"{name} environment variable is not a valid {force_type.__name__}"
        )


# BASE_DIR should point to where manage.py is
if base_dir := env("BASE_DIR", ""):
    BASE_DIR = Path(base_dir)
else:
    raise ImproperlyConfigured("BASE_DIR environment variable is not set")


# Date formats
DATETIME_FORMAT = "H:i Y-m-d"
DATE_FORMAT = "Y-m-d"
TIME_FORMAT = "H:i"


# Site root URL with protocol and without a trailing slash
SITE_ROOT = env("SITE_ROOT", "http://127.0.0.1:8000")


# Site title setting for templates
SITE_TITLE = env("SITE_TITLE", "caves.app")


# Django admin interface URL path
ADMIN_URL = env("ADMIN_URL", "admin/")


# Staff pages URL path
STAFF_URL = env("STAFF_URL", "staff/")


# Imgproxy configuration
IMGPROXY_URL = env("IMGPROXY_URL", "http://127.0.0.1:9000/imgproxy")
IMGPROXY_KEY = env("IMGPROXY_KEY")
IMGPROXY_SALT = env("IMGPROXY_SALT")
IMGPROXY_PRESETS = {
    "tripphoto_thumb": "width=400,height=600,resizing_type=fill",
    "avatar": "width=400,height=400,resizing_type=fill",
    "avatar_navbar": "width=80,height=80,resizing_type=fill",
    "featured_photo": "width=1800,height=800,resizing_type=fill-down",
}

# Security keys/options
# WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS", "http://127.0.0.1").split(" ")
CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS", "http://127.0.0.1").split(" ")

# Need this many for CSV import feature to work - 16 fields per trip
DATA_UPLOAD_MAX_NUMBER_FIELDS = env("DATA_UPLOAD_MAX_NUMBER_FIELDS", 10000, int)

# Add Docker host IP to ALLOWED_HOSTS for Dokku healthchecks
ALLOWED_HOSTS.append(socket.getaddrinfo(socket.gethostname(), "http")[0][4][0])


# Email settings
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", "")
EMAIL_BACKEND = env("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
MAILER_EMAIL_BACKEND = env(
    "MAILER_EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)
MAILER_EMPTY_QUEUE_SLEEP = env("MAILER_EMPTY_QUEUE_SLEEP", 30, int)
EMAIL_HOST = env("EMAIL_HOST", "")
EMAIL_PORT = env("EMAIL_PORT", 0, int)
EMAIL_USE_SSL = env("EMAIL_USE_SSL", False, int)
EMAIL_USE_TLS = env("EMAIL_USE_TLS", False, int)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", "")


# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = False
USE_TZ = True


# Django apps
INSTALLED_APPS = [
    "whitenoise.runserver_nostatic",
    "core.apps.CoreConfig",
    "users.apps.UsersConfig",
    "logger.apps.LoggerConfig",
    "staff.apps.StaffConfig",
    "stats.apps.StatsConfig",
    "import.apps.ImportConfig",
    "export.apps.ExportConfig",
    "comments.apps.CommentsConfig",
    "maps.apps.MapsConfig",
    "dal",
    "dal_select2",
    "django_countries",
    "tinymce",
    "active_link",
    "mailer",
    "crispy_forms",
    "crispy_bootstrap5",
    "django_htmx",
    "markdownify",
    "unfold",
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


# Authentication
LOGIN_URL = "users:login"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
AUTH_USER_MODEL = "users.CavingUser"


# Bootstrap 5 message CSS classes
MESSAGE_TAGS = {
    messages.DEBUG: "alert-secondary",
    messages.INFO: "alert-info",
    messages.SUCCESS: "alert-success",
    messages.WARNING: "alert-warning",
    messages.ERROR: "alert-danger",
}


# Django middleware
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


# Django templates
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates/")],
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


# Django wsgi
WSGI_APPLICATION = "config.django.wsgi.application"


# Django root urlconf
ROOT_URLCONF = "config.django.urls"


# Database
DATABASES = {
    "default": dj_database_url.config(
        default="postgres://postgres:postgres@db:5432/postgres",
        conn_max_age=env("CONN_MAX_AGE", 30, int),
        conn_health_checks=True,
    )
}
DATABASES["default"]["ATOMIC_REQUESTS"] = True
DATABASES["default"]["ENGINE"] = "django.contrib.gis.db.backends.postgis"

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Static files, media files, and Amazon S3.
# Photos are *always* stored in S3, even in development.
AWS_S3_CUSTOM_DOMAIN = env("AWS_S3_CUSTOM_DOMAIN", "")
AWS_S3_ACCESS_KEY_ID = env("AWS_S3_ACCESS_KEY_ID", "")
AWS_S3_SECRET_ACCESS_KEY = env("AWS_S3_SECRET_ACCESS_KEY", "")
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME", "")
AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", "")
AWS_S3_SIGNATURE_VERSION = env("AWS_S3_SIGNATURE_VERSION", "s3v4")
AWS_DEFAULT_ACL = env("AWS_DEFAULT_ACL", "private")
AWS_PRESIGNED_EXPIRY = env("AWS_PRESIGNED_EXPIRY", 20, int)

STATIC_URL = "/static/"
STATIC_ROOT = os.environ.get("STATIC_ROOT", "/app/staticfiles")
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_STORAGE_LOCATION = env("MEDIA_LOCATION", "m")
PHOTOS_STORAGE_LOCATION = env("PHOTOS_LOCATION", "p")

if AWS_STORAGE_BUCKET_NAME:  # pragma: no cover
    MEDIA_URL = env("MEDIA_URL")
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": {
                "location": MEDIA_STORAGE_LOCATION,
            },
        },
        "photos": {
            "BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": {
                "location": PHOTOS_STORAGE_LOCATION,
            },
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
else:
    MEDIA_URL = "/media/"
    MEDIA_ROOT = os.environ.get("MEDIA_ROOT", "/app/mediafiles")
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3.S3Storage",
        },
        "photos": {
            "BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": {
                "location": PHOTOS_STORAGE_LOCATION,
            },
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }


# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Markdownify
MARKDOWNIFY = {
    "default": {
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
    },
    "comment": {
        "WHITELIST_TAGS": [
            "a",
            "strong",
            "blockquote",
            "em",
            "i",
            "b",
        ],
        "LINKIFY_TEXT": {
            "PARSE_URLS": True,
        },
    },
}

MARKDOWNIFY["news"] = copy.deepcopy(MARKDOWNIFY["default"])
MARKDOWNIFY["news"]["WHITELIST_TAGS"].append("img")
MARKDOWNIFY["news"]["WHITELIST_ATTRS"] = ["src", "alt", "title", "class", "href"]

# TinyMCE configuration
TINYMCE_DEFAULT_CONFIG = {
    "theme": "silver",
    "resize": "true",
    "menubar": "file edit view insert format tools table help",
    "toolbar": "undo redo | bold italic underline strikethrough | fontselect fontsizeselect formatselect | alignleft aligncenter alignright alignjustify | outdent indent |  numlist bullist checklist | forecolor backcolor casechange permanentpen formatpainter removeformat | pagebreak | charmap emoticons | fullscreen  preview save print | insertfile image media pageembed template link anchor codesample | a11ycheck ltr rtl | showcomments addcomment code typography",
    "plugins": "advlist autolink lists link image charmap print preview anchor searchreplace visualblocks code fullscreen insertdatetime media table powerpaste advcode help wordcount spellchecker typography",
    "removed_menuitems": "newdocument spellchecker help",
    "height": "500",
}

# Crispy forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"


# Django active link
ACTIVE_LINK_STRICT = True


# Redis
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env("REDIS_URL"),
    }
}


# Logging
DEFAULT_LOG_LEVEL = "ERROR"

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
        "django_logs": {
            "level": env("DJANGO_LOG_LEVEL", DEFAULT_LOG_LEVEL),
            "class": "logging.FileHandler",
            "filename": env("DJANGO_LOG_LOCATION", "/app/logs/django.log"),
            "formatter": "simple",
        },
        "user_actions": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": env("USER_ACTIONS_LOG_LOCATION", "/app/logs/user_actions.log"),
            "formatter": "simple",
        },
        "console": {
            "level": env("DJANGO_LOG_LEVEL", DEFAULT_LOG_LEVEL),
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["django_logs", "console"],
            "level": env("DJANGO_LOG_LEVEL", DEFAULT_LOG_LEVEL),
            "propagate": True,
        },
        "user_actions": {
            "handlers": ["user_actions"],
            "level": "INFO",
        },
    },
}


# Google Maps API Key
GOOGLE_MAPS_PRIVATE_API_KEY = env("GOOGLE_MAPS_PRIVATE_API_KEY", "")
GOOGLE_MAPS_PUBLIC_API_KEY = env("GOOGLE_MAPS_PUBLIC_API_KEY", "")
GOOGLE_MAPS_USER_MAP_ID = env("GOOGLE_MAPS_USER_MAP_ID", "")
