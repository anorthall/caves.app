from django.urls import path
from . import views

app_name = "users"
urlpatterns = [
    path("login/", views.login, name="login"),
    path("logout/", views.logout, name="logout"),
    path("update/", views.update, name="update"),
    path("update/email/", views.update_email, name="email"),
    path("verify/email/", views.verify_email_change, name="verify-email-change"),
    path("verify/resend/", views.resend_verify_email, name="verify-resend"),
    path("verify/", views.verify_new_account, name="verify-new-account"),
    path("profile/", views.profile, name="profile"),
    path("register/", views.register, name="register"),
    path("password/", views.PasswordChangeView.as_view(), name="password"),
    path("password/done", views.password_done, name="password-done"),
]
