from django.urls import include, path

from . import views

app_name = "log"

urlpatterns = [
    path("", views.index, name="index"),
    path("u/<username>/", views.UserProfile.as_view(), name="user"),
    path("trip/<int:pk>/", views.TripDetail.as_view(), name="trip_detail"),
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
    path("statistics/", views.user_statistics, name="statistics"),
    path("admin-tools/", views.admin_tools, name="admin_tools"),
    path("charts/", include("logger.charts_urls")),
]
