from .base import *  # noqa: F403
from .base import STORAGES, env

# Debug should always be off in production
DEBUG = False

# Security settings
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = env("SECURE_SSL_REDIRECT", bool, True)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Sessions
SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
SESSION_CACHE_ALIAS = "default"

# Sentry integration
if env("SENTRY_KEY", str, ""):  # pragma: no cover
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=env("SENTRY_KEY", str),
        integrations=[
            DjangoIntegration(),
        ],
        traces_sample_rate=0.2,
        send_default_pii=True,
    )

# Google Analytics
GOOGLE_ANALYTICS_ID = env("GOOGLE_ANALYTICS_ID", str, "")

# Ratelimiting IP config
RATELIMIT_IP_META_KEY = env("RATELIMIT_IP_META_KEY", str, "HTTP_X_FORWARDED_FOR")

# Compress static files
STORAGES["staticfiles"] = {
    "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
}

# Emails - use django-mailer as the primary backend
EMAIL_BACKEND = "mailer.backend.DbBackend"
MAILER_EMAIL_BACKEND = env(
    "MAILER_EMAIL_BACKEND",
    cast=str,
    default="django.core.mail.backends.smtp.EmailBackend",
)
