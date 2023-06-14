from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.views import View

from .. import services
from ..models import Trip


class CSVExport(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        return render(request, "logger/export.html")

    def post(self, request, *args, **kwargs):
        try:
            http_response = services.generate_csv_export(request.user)
        except Trip.DoesNotExist:
            messages.error(request, "You do not have any trips to export.")
            return redirect("log:export")
        return http_response
