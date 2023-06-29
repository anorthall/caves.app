from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils.safestring import SafeString
from django.views.generic import FormView, View

from . import services
from .forms import ImportUploadForm, TripImportFormset, TripImportFormsetHelper


class Index(LoginRequiredMixin, FormView):
    template_name = "import/index.html"
    form_class = ImportUploadForm
    extra_context = {"trip_types": services.get_trip_types()}


class Sample(View):
    def get(self, request, *args, **kwargs):
        response = HttpResponse(services.generate_sample_csv(), content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="sample_import.csv"'

        return response


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

        # noinspection PyUnboundLocalVariable
        messages.success(request, f"Successfully imported {count} trips!")
        return redirect(request.user.get_absolute_url())