from django.urls import path

from . import views

app_name = "users"
urlpatterns = [
    path("login/", views.login, name="login"),
    path("logout/", views.logout, name="logout"),
    path("email/", views.update_email, name="email"),
    path("profile/", views.Account.as_view(), name="account"),
    path("update/", views.AccountUpdate.as_view(), name="account_update"),
    path("password/", views.PasswordChangeView.as_view(), name="password"),
    path("password/reset/", views.PasswordResetView.as_view(), name="password-reset"),
    path(
        "password/reset/confirm/<uidb64>/<token>/",
        views.PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
    path("register/", views.register, name="register"),
    path("verify/", views.verify_new_account, name="verify-new-account"),
    path("verify/email/", views.verify_email_change, name="verify-email-change"),
    path("verify/resend/", views.resend_verify_email, name="verify-resend"),
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
