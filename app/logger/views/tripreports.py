from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import CreateView, UpdateView
from django_ratelimit.decorators import ratelimit
from core.logging import log_tripreport_action

from ..forms import TripReportForm
from ..mixins import ReportObjectMixin, TripContextMixin, ViewableObjectDetailView
from ..models import Trip, TripReport


@method_decorator(
    ratelimit(key="user", rate="20/h", method=ratelimit.UNSAFE), name="dispatch"
)
class ReportCreate(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = TripReport
    form_class = TripReportForm
    template_name = "logger/trip_report_create.html"
    success_message = "The trip report has been created."
    initial = {
        "pub_date": timezone.localdate,
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.trip = None

    def dispatch(self, request, *args, **kwargs):
        self.trip = self.get_trip()
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        candidate = form.save(commit=False)
        candidate.user = self.request.user
        candidate.trip = self.trip
        candidate.save()
        log_tripreport_action(self.request.user, candidate, "added")
        return super().form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context["trip"] = self.trip
        context["object_owner"] = self.trip.user
        return context

    def get_trip(self):
        trip = get_object_or_404(Trip, uuid=self.kwargs["uuid"])
        if not trip.user == self.request.user:
            raise PermissionDenied
        return trip

    def get(self, request, *args, **kwargs):
        if self.trip.has_report:
            return redirect(self.trip.report.get_absolute_url())

        return super().get(self, request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class ReportDetail(ReportObjectMixin, TripContextMixin, ViewableObjectDetailView):
    model = TripReport
    template_name = "logger/trip_report_detail.html"


class ReportUpdate(
    LoginRequiredMixin, ReportObjectMixin, SuccessMessageMixin, UpdateView
):
    model = TripReport
    form_class = TripReportForm
    template_name = "logger/trip_report_update.html"
    success_message = "The trip report has been updated."

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context["trip"] = self.trip
        context["object_owner"] = self.get_object().user
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_object(self, *args, **kwargs):
        obj = super().get_object(*args, **kwargs)
        if obj.user == self.request.user:
            return obj
        raise PermissionDenied

    def form_valid(self, form):
        log_tripreport_action(self.request.user, self.object, "updated")
        return super().form_valid(form)


class ReportDelete(LoginRequiredMixin, View):
    def post(self, request, uuid):
        try:
            report = get_object_or_404(Trip, uuid=uuid).report
        except TripReport.DoesNotExist:
            raise Http404

        if not report.user == request.user:
            raise PermissionDenied

        trip = report.trip
        log_tripreport_action(request.user, report, "deleted")
        report.delete()
        messages.success(
            request,
            f"The trip report for the trip to {trip.cave_name} has been deleted.",
        )
        return redirect(trip.get_absolute_url())
