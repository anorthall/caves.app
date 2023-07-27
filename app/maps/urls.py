from django.urls import path

from . import views

app_name = "maps"
urlpatterns = [
    path("geocoding/", views.HTMXGeocoding.as_view(), name="geocoding"),
]