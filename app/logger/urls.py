from django.urls import path, include
from . import views

app_name = "log"

urlpatterns = [
    path("", views.index, name="index"),
    path("trip/<int:pk>/", views.TripDetailView.as_view(), name="trip_detail"),
    path("trip/edit/<int:pk>/", views.TripUpdateView.as_view(), name="trip_update"),
    path("trip/delete/<int:pk>/", views.TripDeleteView.as_view(), name="trip_delete"),
    path("trip/add/", views.TripCreateView.as_view(), name="trip_create"),
    path("trips/", views.TripListView.as_view(), name="trip_list"),
    path("trips/export/", views.export, name="export"),
    path("report/<int:pk>/", views.ReportDetailView.as_view(), name="report_detail"),
    path(
        "report/add/<int:pk>/", views.ReportCreateView.as_view(), name="report_create"
    ),
    path(
        "report/edit/<int:pk>/", views.ReportUpdateView.as_view(), name="report_update"
    ),
    path(
        "report/delete/<int:pk>/",
        views.ReportDeleteView.as_view(),
        name="report_delete",
    ),
    path("statistics/", views.user_statistics, name="statistics"),
    path("admin-tools/", views.admin_tools, name="admin_tools"),
    path("charts/", include("logger.charts_urls")),
]
