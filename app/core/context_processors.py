from django.conf import settings


def site_root(request):
    """Add the SITE_ROOT setting to the context"""
    return {"site_root": settings.SITE_ROOT}


def site_title(request):
    """Add the SITE_TITLE setting to the context"""
    return {"site_title": settings.SITE_TITLE}


def api_keys(request):
    """Add relevant API keys to the context"""
    context = {}
    if hasattr(settings, "GOOGLE_ANALYTICS_ID"):
        context["google_analytics_id"] = settings.GOOGLE_ANALYTICS_ID

    if hasattr(settings, "GOOGLE_MAPS_PUBLIC_API_KEY"):
        context["google_maps_api_key"] = settings.GOOGLE_MAPS_PUBLIC_API_KEY

    return context
