from django.conf import settings


def site_root(request):
    """Add the SITE_ROOT setting to the context"""
    return {"site_root": settings.SITE_ROOT}
