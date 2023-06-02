from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("help/", views.Help.as_view(), name="help"),
    path("400/", views.HTTP400.as_view(), name="400"),
    path("403/", views.HTTP403.as_view(), name="403"),
    path("403_csrf/", views.HTTP403CSRF.as_view(), name="403_csrf"),
    path("404/", views.HTTP404.as_view(), name="404"),
    path("500/", views.HTTP500.as_view(), name="500"),
]
