from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import redirect
from django.views.generic import TemplateView

from .forms import TripExportForm
from .services import TripExporter


class Index(LoginRequiredMixin, TemplateView):
    template_name = "export/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = TripExportForm
        return context

    def post(self, request, *args, **kwargs):  # TODO: Email the output
        form = TripExportForm(request.POST)
        if not form.is_valid():
            messages.error(
                request,
                (
                    "There was an error generating your download. "
                    "Did you select a valid format?"
                ),
            )
            return redirect("export:index")

        file_type = form.cleaned_data["format"]
        match file_type:
            case "csv":
                format = "text/csv"
            case "json":
                format = "application/json"
            case _:  # pragma: no cover
                format = "text/plain"

        exporter = TripExporter(user=request.user, queryset=request.user.trips)
        data = exporter.generate().export(file_type)
        return HttpResponse(
            data,
            content_type=format,
            headers={"Content-Disposition": f"attachment; filename=trips.{file_type}"},
        )
