from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("logger.urls")),
    path("", include("core.urls")),
    path("account/", include("users.urls")),
    path("admin/", admin.site.urls),
    path("tinymce/", include("tinymce.urls")),
]

if settings.DEBUG:
    urlpatterns += [path("__debug__/", include("debug_toolbar.urls"))]
