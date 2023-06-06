from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("logger.urls")),
    path("", include("core.urls")),
    path("stats/", include("stats.urls")),
    path("account/", include("users.urls")),
    path(settings.STAFF_URL, include("staff.urls")),
    path(settings.ADMIN_URL, admin.site.urls),
    path("tinymce/", include("tinymce.urls")),
]

if settings.DEBUG:
    from django.conf.urls.static import static

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [path("__debug__/", include("debug_toolbar.urls"))]
