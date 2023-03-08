from django.urls import path
from . import views

app_name = "users"
urlpatterns = [
    path("login/", views.login, name="login"),
    path("logout/", views.logout, name="logout"),
    path("update/", views.update, name="update"),
    path("email/", views.update_email, name="email"),
    path("profile/", views.profile, name="profile"),
    path("password/", views.PasswordChangeView.as_view(), name="password"),
    path("password/done/", views.password_reset_done, name="password-reset-done"),
    path("password/reset/", views.PasswordResetView.as_view(), name="password-reset"),
    path(
        "password/reset/confirm/<uidb64>/<token>/",
        views.PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
    path("password/reset/sent/", views.password_reset_sent, name="password-reset-sent"),
    path("register/", views.register, name="register"),
    path("verify/", views.verify_new_account, name="verify-new-account"),
    path("verify/email/", views.verify_email_change, name="verify-email-change"),
    path("verify/resend/", views.resend_verify_email, name="verify-resend"),
]
