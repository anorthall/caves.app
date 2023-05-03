from django.urls import path

from . import views

# fmt: off
app_name = "users"
urlpatterns = [
    path("login/", views.Login.as_view(), name="login"),
    path("logout/", views.Logout.as_view(), name="logout"),
    path("email/", views.UpdateEmail.as_view(), name="email"),
    path("view/", views.Account.as_view(), name="account_detail"),
    path("update/", views.AccountUpdate.as_view(), name="account_update"),
    path("password/", views.PasswordChangeView.as_view(), name="password_update"),
    path("password/reset/", views.PasswordResetView.as_view(), name="password_reset"),
    path("password/reset/confirm/<uidb64>/<token>/", views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),  # noqa E501
    path("register/", views.register, name="register"),
    path("verify/", views.verify_new_account, name="verify_new_account"),
    path("verify/email/", views.VerifyEmailChange.as_view(), name="verify_email_change"),  # noqa E501
    path("verify/resend/", views.resend_verify_email, name="verify_resend"),
    path("friends/", views.FriendListView.as_view(), name="friends"),
    path("friends/remove/<slug:username>/", views.FriendRemoveView.as_view(), name="friend_remove"),  # noqa E501
    path("friends/add/", views.FriendAddView.as_view(), name="friend_add"),
    path("friends/request/delete/<int:pk>/", views.FriendRequestDeleteView.as_view(), name="friend_request_delete"),  # noqa E501
    path("friends/request/accept/<int:pk>/", views.FriendRequestAcceptView.as_view(), name="friend_request_accept"),  # noqa E501
    path("n/<int:pk>/", views.NotificationRedirect.as_view(), name="notification"),
]
