from django.conf import settings


def site_root(request):
    """Add the SITE_ROOT setting to the context"""
    return {"site_root": settings.SITE_ROOT}


def site_title(request):
    """Add the SITE_TITLE setting to the context"""
    return {"site_title": settings.SITE_TITLE}


def google_analytics(request):
    """Add the GOOGLE_ANALYTICS_ID setting to the context"""
    if settings.GOOGLE_ANALYTICS_ID:
        return {"google_analytics_id": settings.GOOGLE_ANALYTICS_ID}
    return {}
