from django.urls import path
from . import views

app_name = "users"
urlpatterns = [
    path("login/", views.login, name="login"),
    path("logout/", views.logout, name="logout"),
    path("update/", views.update, name="update"),
    path("profile/", views.profile, name="profile"),
    path("register/", views.register, name="register"),
    path("verify/", views.verify_email, name="verify"),
    path("password/", views.PasswordChangeView.as_view(), name="password"),
    path("password/done", views.password_done, name="password-done"),
]
