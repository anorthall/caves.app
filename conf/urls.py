from django.conf import settings
from django.contrib import admin
from django.urls import URLPattern, URLResolver, include, path

urlpatterns: list[URLPattern | URLResolver] = [
    path("", include("core.urls")),
    path("", include("logger.urls")),
    path("map/", include("maps.urls")),
    path("comments/", include("comments.urls")),
    path("statistics/", include("stats.urls")),
    path("account/", include("users.urls")),
    path("export/", include("data_export.urls")),
    path("import/", include("data_import.urls")),
    path(settings.STAFF_URL, include("staff.urls")),
    path(settings.ADMIN_URL, admin.site.urls),
]

if settings.DEBUG:
    from django.conf.urls.static import static

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [path("__debug__/", include("debug_toolbar.urls"))]
    urlpatterns += [path("__reload__/", include("django_browser_reload.urls"))]
