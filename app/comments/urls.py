from django.urls import path

from . import views

app_name = "comments"
urlpatterns = [
    path("add/<uuid:uuid>/", views.AddComment.as_view(), name="add"),
    path("delete/<uuid:uuid>/", views.DeleteComment.as_view(), name="delete"),
    path("htmx/<uuid:uuid>/", views.HTMXTripComment.as_view(), name="htmx_comments"),
]
