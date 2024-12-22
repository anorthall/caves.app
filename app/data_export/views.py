from core.logging import log_user_action
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django_ratelimit.decorators import ratelimit

from .forms import TripExportForm
from .services import TripExporter


@method_decorator(ratelimit(key="user", rate="100/d", method=ratelimit.UNSAFE), name="dispatch")
class Index(LoginRequiredMixin, TemplateView):
    template_name = "export/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = TripExportForm
        return context

    def post(self, request, *args, **kwargs):
        form = TripExportForm(request.POST)
        if not form.is_valid():
            messages.error(
                request,
                ("There was an error generating your download. " "Did you select a valid format?"),
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

        num_trips = request.user.trips.count()
        log_user_action(request.user, f"exported {num_trips} trips to a {file_type.upper()} file")
        return HttpResponse(
            data,
            content_type=format,
            headers={
                "Content-Disposition": f"attachment; filename=trips.{file_type}"  # noqa: E702 E501
            },
        )
