from django.urls import include, path

from . import views

app_name = "log"

# fmt: off
urlpatterns = [
    path("", views.Index.as_view(), name="index"),
    path("u/<username>/", views.UserProfile.as_view(), name="user"),
    path("trips/", views.TripsRedirect.as_view(), name="trip_list"),
    path("trips/export/", views.CSVExport.as_view(), name="export"),
    path("trip/<int:pk>/", views.TripDetail.as_view(), name="trip_detail"),
    path("trip/<int:pk>/like", views.HTMXTripLike.as_view(), name="trip_like_htmx_view"),  # noqa E501
    path("trip/edit/<int:pk>/", views.TripUpdate.as_view(), name="trip_update"),
    path("trip/delete/<int:pk>/", views.TripDelete.as_view(), name="trip_delete"),
    path("trip/add/", views.TripCreate.as_view(), name="trip_create"),
    path("report/<int:pk>/", views.ReportDetail.as_view(), name="report_detail"),
    path("report/add/<int:pk>/", views.ReportCreate.as_view(), name="report_create"),
    path("report/edit/<int:pk>/", views.ReportUpdate.as_view(), name="report_update"),
    path("report/delete/<int:pk>/", views.ReportDelete.as_view(), name="report_delete"),
    path("feed/htmx/", views.HTMXFeed.as_view(), name="feed_htmx_view"),
    path("feed/set_ordering/", views.SetFeedOrdering.as_view(), name="feed_set_ordering"),  # noqa E501
    # TODO: Refactor comments
    # path("comment/add/", views.AddComment.as_view(), name="comment_add"),
    # path("comment/delete/<int:pk>/", views.DeleteComment.as_view(), name="comment_delete"),  # noqa E501
    # path("comment/htmxtrip/<int:pk>/", views.HTMXTripComment.as_view(), name="htmx_trip_comment"),  # noqa E501
    path("statistics/", views.user_statistics, name="statistics"),
    path("admin-tools/", views.AdminTools.as_view(), name="admin_tools"),
    path("charts/", include("logger.charts_urls")),
]
