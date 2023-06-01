from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("help/", views.Help.as_view(), name="help"),
]
