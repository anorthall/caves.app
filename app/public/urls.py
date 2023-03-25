from django.urls import path
from . import views

app_name = "public"
urlpatterns = [
    path("<slug:username>/", views.user, name="user"),
    path("<slug:username>/trip/<int:pk>/", views.trip, name="trip"),
]
