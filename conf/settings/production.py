from .base import *  # noqa: F403
from .base import STORAGES, env

# Debug should always be off in production
DEBUG = False

# Sessions
SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

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

# Emails
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
MAILER_EMAIL_BACKEND = env("MAILER_EMAIL_BACKEND", cast=str, default=EMAIL_BACKEND)
