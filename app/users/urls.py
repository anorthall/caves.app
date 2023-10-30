from django.urls import path

from . import views

app_name = "users"
urlpatterns = [
    path("login/", views.Login.as_view(), name="login"),
    path("logout/", views.Logout.as_view(), name="logout"),
    path("view/", views.Account.as_view(), name="account_detail"),
    path("settings/", views.AccountSettings.as_view(), name="account_settings"),
    path(
        "custom-fields/",
        views.CustomFieldsUpdate.as_view(),
        name="custom_fields_update",
    ),
    path("profile/", views.ProfileUpdate.as_view(), name="profile_update"),
    path("profile/photo/", views.AvatarUpdate.as_view(), name="profile_photo_update"),
    path("password/reset/", views.PasswordResetView.as_view(), name="password_reset"),
    path(
        "password/reset/confirm/<uidb64>/<token>/",
        views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path("register/", views.register, name="register"),
    path("verify/", views.verify_new_account, name="verify_new_account"),
    path(
        "verify/email/", views.VerifyEmailChange.as_view(), name="verify_email_change"
    ),
    path("verify/resend/", views.resend_verify_email, name="verify_resend"),
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
    path(
        "notifications/dropdown/",
        views.HTMXNotificationsDropdown.as_view(),
        name="htmx_notifications_dropdown",
    ),
    path(
        "notifications/<int:pk>/",
        views.NotificationRedirect.as_view(),
        name="notification",
    ),
    path(
        "notifications/list/", views.NotificationsList.as_view(), name="notifications"
    ),
    path(
        "notifications/clear/",
        views.NotificationMarkAllRead.as_view(),
        name="notifications_mark_read",
    ),
]
