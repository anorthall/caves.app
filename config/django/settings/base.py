import os
from pathlib import Path
from typing import Any

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
base_dir = env("BASE_DIR", "")
if base_dir:
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
    "avatar": "width=450,height=450,resizing_type=fill",
    "avatar_navbar": "width=60,height=60,resizing_type=fill",
}

# Security keys/options
# WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS", "http://127.0.0.1").split(" ")
CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS", "http://127.0.0.1").split(" ")
# need this many for CSV import feature to work - 16 fields per trip
DATA_UPLOAD_MAX_NUMBER_FIELDS = env("DATA_UPLOAD_MAX_NUMBER_FIELDS", 10000, int)


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
    "core.apps.CoreConfig",
    "users.apps.UsersConfig",
    "logger.apps.LoggerConfig",
    "staff.apps.StaffConfig",
    "stats.apps.StatsConfig",
    "import.apps.ImportConfig",
    "export.apps.ExportConfig",
    "comments.apps.CommentsConfig",
    "django_countries",
    "tinymce",
    "active_link",
    "mailer",
    "crispy_forms",
    "crispy_bootstrap5",
    "django_htmx",
    "markdownify.apps.MarkdownifyConfig",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django.contrib.postgres",
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
                "users.context_processors.notifications",
                "core.context_processors.site_root",
                "core.context_processors.site_title",
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
    "default": {
        "ENGINE": env("SQL_ENGINE", "django.db.backends.sqlite3"),
        "NAME": env("SQL_DATABASE", BASE_DIR / "db.sqlite3"),
        "USER": env("SQL_USER", "user"),
        "PASSWORD": env("SQL_PASSWORD", "password"),
        "HOST": env("SQL_HOST", "localhost"),
        "PORT": env("SQL_PORT", "5432", int),
        "ATOMIC_REQUESTS": env("SQL_ATOMIC_REQUESTS", True, int),
    }
}
CONN_MAX_AGE = env("CONN_MAX_AGE", 30, int)


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


# Amazon S3
AWS_S3_CUSTOM_DOMAIN = env("AWS_S3_CUSTOM_DOMAIN", "")
AWS_S3_ACCESS_KEY_ID = env("AWS_S3_ACCESS_KEY_ID", "")
AWS_S3_SECRET_ACCESS_KEY = env("AWS_S3_SECRET_ACCESS_KEY", "")
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME", "")
AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", "")
AWS_S3_SIGNATURE_VERSION = env("AWS_S3_SIGNATURE_VERSION", "s3v4")
AWS_DEFAULT_ACL = env("AWS_DEFAULT_ACL", "private")
AWS_PRESIGNED_EXPIRY = env("AWS_PRESIGNED_EXPIRY", 20, int)


# Storages
STORAGES = {
    "photos": {
        "BACKEND": "core.custom_storages.PhotosS3Storage",
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
