"""
caves.app settings
"""
import os, socket
from pathlib import Path
from django.contrib.messages import constants as messages

BASE_DIR = Path(__file__).resolve().parent.parent


########################
# App specific options #
########################

# Date formats
DATETIME_FORMAT = "H:i Y-m-d"
DATE_FORMAT = "Y-m-d"
TIME_FORMAT = "H:i"

# Site root URL with protocol
SITE_ROOT = os.environ.get("SITE_ROOT", "http://127.0.0.1:8000")

# Security keys/options
# WARNING: keep the secret key used in production secret!
# WARNING: do not run with debug on in production!
SECRET_KEY = os.environ.get("SECRET_KEY")
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS").split(" ")
DEBUG = int(os.environ.get("DEBUG", default=0))
CSRF_TRUSTED_ORIGINS = os.environ.get("CSRF_TRUSTED_ORIGINS").split(" ")


##################
# Email settings #
##################

DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL")
EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)
MAILER_EMAIL_BACKEND = os.environ.get(
    "MAILER_EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)
MAILER_EMPTY_QUEUE_SLEEP = int(os.environ.get("MAILER_EMPTY_QUEUE_SLEEP", 30))
EMAIL_HOST = os.environ.get("EMAIL_HOST", None)
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 0))
EMAIL_USE_SSL = int(os.environ.get("EMAIL_USE_SSL", 0))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", None)
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", None)


################################
# Django/django plugin options #
################################

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = False
USE_TZ = True

# Django plugin settings
ACTIVE_LINK_STRICT = True  # django-active-link

# Django apps
INSTALLED_APPS = [
    "core.apps.CoreConfig",
    "users.apps.UsersConfig",
    "logger.apps.LoggerConfig",
    "public.apps.PublicConfig",
    "social.apps.SocialConfig",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "widget_tweaks",
    "django_countries",
    "tinymce",
    "active_link",
    "mailer",
    "crispy_forms",
    "crispy_bootstrap5",
    "markdownify.apps.MarkdownifyConfig",
    "debug_toolbar",
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
    "users.middleware.TimezoneMiddleware",
    "users.middleware.LastSeenMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
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
                "social.context_processors.notifications",
            ],
        },
    },
]

# Django wsgi
WSGI_APPLICATION = "cavinglog.wsgi.application"

# Django root urlconf
ROOT_URLCONF = "cavinglog.urls"

# Database
DATABASES = {
    "default": {
        "ENGINE": os.environ.get("SQL_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.environ.get("SQL_DATABASE", BASE_DIR / "db.sqlite3"),
        "USER": os.environ.get("SQL_USER", "user"),
        "PASSWORD": os.environ.get("SQL_PASSWORD", "password"),
        "HOST": os.environ.get("SQL_HOST", "localhost"),
        "PORT": os.environ.get("SQL_PORT", "5432"),
    }
}

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

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATIC_ROOT = os.environ.get("STATIC_ROOT", "/opt/caves/staticfiles")
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Debug toolbar for Docker
if DEBUG:
    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS = [ip[: ip.rfind(".")] + ".1" for ip in ips] + [
        "127.0.0.1",
        "10.0.2.2",
    ]

# Sentry SDK
if not DEBUG and os.environ.get("SENTRY_KEY", None):
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=os.environ.get("SENTRY_KEY"),
        integrations=[
            DjangoIntegration(),
        ],
        traces_sample_rate=1.0,
        send_default_pii=True,
    )

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
    }
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
