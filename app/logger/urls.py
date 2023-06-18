from django.urls import include, path

from . import views

app_name = "log"

urlpatterns = [
    path("", views.Index.as_view(), name="index"),
    path("u/<slug:username>/", views.UserProfile.as_view(), name="user"),
    path("trips/", views.TripsRedirect.as_view(), name="trip_list"),
    path("trips/export/", views.CSVExport.as_view(), name="export"),
    path("trip/edit/<uuid:uuid>/", views.TripUpdate.as_view(), name="trip_update"),
    path("trip/delete/<uuid:uuid>/", views.TripDelete.as_view(), name="trip_delete"),
    path("trip/add/", views.TripCreate.as_view(), name="trip_create"),
    path(
        "trip/like/<uuid:uuid>/",
        views.HTMXTripLike.as_view(),
        name="trip_like_htmx_view",
    ),
    path("trip/<uuid:uuid>/", views.TripDetail.as_view(), name="trip_detail"),
    path("trip/<uuid:uuid>/photos/", views.TripPhotos.as_view(), name="trip_photos"),
    path(
        "trip/<uuid:uuid>/photos/delete/all/",
        views.TripPhotosDeleteAll.as_view(),
        name="trip_photos_delete_all",
    ),
    path(
        "trip/photos/upload/",
        views.TripPhotosUpload.as_view(),
        name="trip_photos_upload",
    ),
    path(
        "trip/photos/upload/success/",
        views.TripPhotosUploadSuccess.as_view(),
        name="trip_photos_upload_success",
    ),
    path(
        "trip/photos/delete/",
        views.TripPhotosDelete.as_view(),
        name="trip_photos_delete",
    ),
    path(
        "trip/photos/update/",
        views.TripPhotosUpdate.as_view(),
        name="trip_photos_update",
    ),
    path("report/add/<uuid:uuid>/", views.ReportCreate.as_view(), name="report_create"),
    path(
        "report/edit/<uuid:uuid>/", views.ReportUpdate.as_view(), name="report_update"
    ),
    path(
        "report/delete/<uuid:uuid>/", views.ReportDelete.as_view(), name="report_delete"
    ),
    path("report/<uuid:uuid>/", views.ReportDetail.as_view(), name="report_detail"),
    path("search/", views.Search.as_view(), name="search"),
    path("feed/htmx/", views.HTMXTripFeed.as_view(), name="feed_htmx_view"),
    path(
        "feed/set_ordering/", views.SetFeedOrdering.as_view(), name="feed_set_ordering"
    ),
    path("statistics/", views.user_statistics, name="statistics"),
    path("charts/", include("logger.charts_urls")),
]
