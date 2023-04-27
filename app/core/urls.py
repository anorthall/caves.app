from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("about/", views.About.as_view(), name="about"),
    path("help/", views.Help.as_view(), name="help"),
]
