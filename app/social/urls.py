from django.urls import path

from . import views

app_name = "social"

urlpatterns = [
    path("friends/", views.FriendListView.as_view(), name="friends"),
    path(
        "friends/remove/<slug:username>/",
        views.FriendRemoveView.as_view(),
        name="friend_remove",
    ),
    path("friends/add/", views.FriendAddView.as_view(), name="friend_add"),
    path(
        "friends/request/delete/<int:pk>/",
        views.FriendRequestDeleteView.as_view(),
        name="friend_request_delete",
    ),
    path(
        "friends/request/accept/<int:pk>/",
        views.FriendRequestAcceptView.as_view(),
        name="friend_request_accept",
    ),
    path("n/<int:pk>/", views.notification_redirect, name="notification"),
]
