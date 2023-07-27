from django.urls import path

from . import views

app_name = "maps"
urlpatterns = [
    path("geocoding/", views.HTMXGeocoding.as_view(), name="geocoding"),
    path("location/", views.FindTripToAddLocation.as_view(), name="add_location"),
    path(
        "location/<uuid:trip>/",
        views.AddTripLocation.as_view(),
        name="add_location_form",
    ),
    path("", views.UserMap.as_view(), name="index"),
]
