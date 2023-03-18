from django.urls import path
from . import views

app_name = "log"
urlpatterns = [
    path("", views.index, name="index"),
    path("trip/<int:pk>/", views.TripDetailView.as_view(), name="trip_detail"),
    path("trip/edit/<int:pk>/", views.TripUpdateView.as_view(), name="trip_update"),
    path("trip/delete/<int:pk>/", views.TripDeleteView.as_view(), name="trip_delete"),
    path("trip/delete/success/", views.trip_deleted, name="trip_deleted"),
    path("trip/add/", views.TripCreateView.as_view(), name="trip_create"),
    path("trips/", views.TripListView.as_view(), name="trip_list"),
    path("about/", views.about, name="about"),
]
