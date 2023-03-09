from django.urls import path
from . import views

app_name = "log"
urlpatterns = [
    path("", views.index, name="index"),
    path("edit/<int:pk>/", views.TripUpdateView.as_view(), name="trip_update"),
    path("trip/<int:pk>/", views.TripDetailView.as_view(), name="trip_detail"),
]
