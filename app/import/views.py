from core.logging import log_user_action
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.utils.safestring import SafeString
from django.views.generic import FormView, View
from django_ratelimit.decorators import ratelimit
from logger.models import Caver

from . import services
from .forms import ImportUploadForm, TripImportFormset, TripImportFormsetHelper


@method_decorator(
    ratelimit(key="user", rate="30/h", method=ratelimit.UNSAFE, group="import"),
    name="dispatch",
)
class Index(LoginRequiredMixin, FormView):
    template_name = "import/index.html"
    form_class = ImportUploadForm
    extra_context = {"trip_types": services.get_trip_types()}


@method_decorator(ratelimit(key="user", rate="30/h"), name="dispatch")
class Sample(View):
    def get(self, request, *args, **kwargs):
        response = HttpResponse(services.generate_sample_csv(), content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="sample_import.csv"'

        return response


@method_decorator(
    ratelimit(key="user", rate="30/h", method=ratelimit.UNSAFE, group="import"),
    name="dispatch",
)
class Process(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        form = ImportUploadForm(request.POST, request.FILES)
        if not form.is_valid():
            error_msg = (
                "<strong>Error:</strong> Unable to process the uploaded file. "
                "Please check that you are uploading a CSV file with between 1 "
                "and 50 data rows. "
            )
            messages.error(request, SafeString(error_msg))
            return redirect("import:index")

        data = form.cleaned_data["file"]
        formset = services.get_formset_with_data(data)
        context = {"formset": formset, "helper": TripImportFormsetHelper()}

        return render(request, "import/process.html", context)


@method_decorator(
    ratelimit(key="user", rate="30/h", method=ratelimit.UNSAFE, group="import"),
    name="dispatch",
)
class Save(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        formset = TripImportFormset(request.POST)
        context = {"formset": formset, "helper": TripImportFormsetHelper()}

        if not formset.is_valid():
            messages.error(
                request,
                "Not all fields have been completed and/or some fields have errors. "
                "Please review the messages below to resolve the issues.",
            )
            return render(request, "import/process.html", context)

        # Save the data to trip objects
        for count, form in enumerate(formset, 1):
            trip = form.save(commit=False)
            trip.user = request.user
            trip.save()

            trip.followers.add(request.user)

            cavers = form.cleaned_data["cavers"]
            cavers = cavers.split(",")
            for caver in cavers:
                if caver := caver.strip():
                    caver_obj, _ = Caver.objects.get_or_create(
                        name=caver, user=request.user
                    )
                    trip.cavers.add(caver_obj)

        # noinspection PyUnboundLocalVariable
        messages.success(request, f"Successfully imported {count} trips!")
        log_user_action(request.user, f"imported {count} trips from a CSV file")
        return redirect(request.user.get_absolute_url())
