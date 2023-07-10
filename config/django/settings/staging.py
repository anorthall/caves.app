from .production import *

# Turn DEBUG on in staging
DEBUG = True

# Turn staticfiles off in staging to serve from CDN
INSTALLED_APPS.remove("django.contrib.staticfiles")

# Django debug toolbar
INSTALLED_APPS += ["debug_toolbar"]
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]

# Always show the toolbar in staging as staging should never be exposed
# to the internet anyway
DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda request: True,
}
