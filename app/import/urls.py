from django.urls import path

from . import views

app_name = "import"
urlpatterns = [
    path("", views.Index.as_view(), name="index"),
    path("sample/", views.Sample.as_view(), name="sample"),
    path("process/", views.Process.as_view(), name="process"),
    path("save/", views.Save.as_view(), name="save"),
]
