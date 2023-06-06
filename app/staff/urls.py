from django.urls import path

from . import views

app_name = "staff"

# fmt: off
urlpatterns = [
    path("", views.Dashboard.as_view(), name="dashboard"),
    path("index/", views.Index.as_view(), name="index"),
]
