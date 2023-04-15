from django.urls import path
from . import views


app_name = "social"

urlpatterns = [
    path("n/<int:pk>/", views.notification_redirect, name="notification"),
]
