from django.urls import path

from . import views

app_name = "log"

urlpatterns = [
    path("", views.Index.as_view(), name="index"),
    path("u/<slug:username>/", views.UserProfile.as_view(), name="user"),
    path("trips/", views.TripsRedirect.as_view(), name="trip_list"),
    path("trip/edit/<uuid:uuid>/", views.TripUpdate.as_view(), name="trip_update"),
    path("trip/delete/<uuid:uuid>/", views.TripDelete.as_view(), name="trip_delete"),
    path("trip/add/", views.TripCreate.as_view(), name="trip_create"),
    path(
        "trip/like/<uuid:uuid>/",
        views.HTMXTripLike.as_view(),
        name="trip_like_htmx_view",
    ),
    path(
        "trip/follow/<uuid:uuid>/",
        views.HTMXTripFollow.as_view(),
        name="trip_follow_htmx_view",
    ),
    path("trip/<uuid:uuid>/", views.TripDetail.as_view(), name="trip_detail"),
    path("trip/<uuid:uuid>/photos/", views.TripPhotos.as_view(), name="trip_photos"),
    path(
        "trip/<uuid:uuid>/photos/feature/",
        views.TripPhotoFeature.as_view(),
        name="trip_photos_feature",
    ),
    path(
        "trip/<uuid:uuid>/photos/unfeature/",
        views.TripPhotoUnsetFeature.as_view(),
        name="trip_photos_unfeature",
    ),
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
    path("log/cavers/", views.CaverList.as_view(), name="caver_list"),
    path("log/cavers/<uuid:uuid>/", views.CaverDetail.as_view(), name="caver_detail"),
    path(
        "log/cavers/<uuid:uuid>/delete/",
        views.CaverDelete.as_view(),
        name="caver_delete",
    ),
    path(
        "log/cavers/<uuid:uuid>/rename/",
        views.CaverRename.as_view(),
        name="caver_rename",
    ),
    path("log/cavers/<uuid:uuid>/link/", views.CaverLink.as_view(), name="caver_link"),
    path(
        "log/cavers/<uuid:uuid>/unlink/",
        views.CaverUnlink.as_view(),
        name="caver_unlink",
    ),
    path("log/cavers/<uuid:uuid>/merge/", views.CaverMerge.as_view(), name="caver_merge"),
    path(
        "log/cavers/autocomplete",
        views.CaverAutocomplete.as_view(create_field="name", validate_create=True),
        name="caver_autocomplete",
    ),
    path("report/<uuid:uuid>/", views.TripReportRedirect.as_view(), name="report_detail"),
    path("search/", views.Search.as_view(), name="search"),
    path("feed/htmx/", views.HTMXTripFeed.as_view(), name="feed_htmx_view"),
    path("feed/set_ordering/", views.SetFeedOrdering.as_view(), name="feed_set_ordering"),
]
