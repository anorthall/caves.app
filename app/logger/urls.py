from django.urls import include, path

from . import views

app_name = "log"

urlpatterns = [
    path("", views.index, name="index"),
    path("u/<username>/", views.UserProfile.as_view(), name="user"),
    path("trip/<int:pk>/", views.TripDetail.as_view(), name="trip_detail"),
    path("trip/<int:pk>/like", views.TripLikeToggle.as_view(), name="trip_like"),
    path("trip/edit/<int:pk>/", views.TripUpdate.as_view(), name="trip_update"),
    path("trip/delete/<int:pk>/", views.TripDelete.as_view(), name="trip_delete"),
    path("trip/add/", views.TripCreate.as_view(), name="trip_create"),
    path("trips/", views.trips_redirect, name="trip_list"),
    path("trips/export/", views.export, name="export"),
    path("report/<int:pk>/", views.ReportDetail.as_view(), name="report_detail"),
    path("report/add/<int:pk>/", views.ReportCreate.as_view(), name="report_create"),
    path("report/edit/<int:pk>/", views.ReportUpdate.as_view(), name="report_update"),
    path(
        "report/delete/<int:pk>/",
        views.ReportDelete.as_view(),
        name="report_delete",
    ),
    path("comment/add/", views.AddComment.as_view(), name="comment_add"),
    path(
        "comment/delete/<int:pk>/", views.DeleteComment.as_view(), name="comment_delete"
    ),
    path(
        "comment/htmxtrip/<int:pk>/",
        views.HTMXTripComment.as_view(),
        name="htmx_trip_comment",
    ),
    path("statistics/", views.user_statistics, name="statistics"),
    path("admin-tools/", views.admin_tools, name="admin_tools"),
    path("charts/", include("logger.charts_urls")),
]
