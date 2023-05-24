import os

from .base import *

# Debug should always be off in production
DEBUG = False


# Sentry integration
if os.environ.get("SENTRY_KEY", None):  # pragma: no cover
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


# Google Analytics
GOOGLE_ANALYTICS_ID = os.environ.get("GOOGLE_ANALYTICS_ID", None)

if GOOGLE_ANALYTICS_ID:  # pragma: no cover
    TEMPLATES["OPTIONS"]["context_processors"] += [
        "core.context_processors.google_analytics",
    ]
