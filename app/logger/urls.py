from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("edit/<int:pk>/", views.TripUpdateView.as_view(), name="trip_update"),
]
