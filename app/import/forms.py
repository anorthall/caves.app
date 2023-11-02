import copy
import csv

import chardet
import magic
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Field, Fieldset, Layout, Submit
from django import forms
from django.core.exceptions import ValidationError
from django.urls import reverse
from logger.forms import BaseTripForm
from logger.models import Trip

from .services import get_headers


class ImportUploadForm(forms.Form):
    file = forms.FileField(
        label="Import file",
        help_text="Upload a CSV file containing trip data",
        required=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["file"].widget.attrs.update({"accept": ".csv"})
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_action = reverse("import:process")
        self.helper.add_input(Submit("submit", "Upload"))

    def clean_file(self) -> list[dict]:
        # Check that the file is a CSV file
        file = self.cleaned_data["file"]

        file_copy = copy.deepcopy(file)
        mime = magic.from_buffer(file_copy.read(), mime=True)
        if mime not in ["text/csv", "text/plain"]:
            raise ValidationError("The imported file is not a CSV file.")

        raw_data = file.read()
        encoding = chardet.detect(raw_data)["encoding"]
        csv_data = csv.DictReader(
            raw_data.decode(encoding).splitlines(), fieldnames=get_headers()
        )

        # Remove the header row and any blank rows
        cleaned_rows = []
        for i, row in enumerate(csv_data):
            if i == 0:
                continue

            if not any(row.values()):
                continue

            cleaned_rows.append(row)

        # Check the file is not too small or large
        if not cleaned_rows:
            raise ValidationError("Imported file has no data rows.")

        if len(cleaned_rows) > 50:
            raise ValidationError("Imported file has more than 50 data rows.")

        return cleaned_rows


class TripImportForm(BaseTripForm):
    cavers = forms.CharField(
        max_length=255,
        label="Cavers",
        help_text="A comma separated list of cavers.",
        required=False,
    )

    class Meta:
        model = Trip
        fields = [
            "cave_name",
            "cave_entrance",
            "cave_exit",
            "cave_region",
            "cave_country",
            "start",
            "end",
            "type",
            "privacy",
            "clubs",
            "expedition",
            "horizontal_dist",
            "vert_dist_down",
            "vert_dist_up",
            "surveyed_dist",
            "resurveyed_dist",
            "aid_dist",
            "notes",
        ]
        widgets = {
            "start": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "end": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


# noinspection PyTypeChecker
class TripImportFormsetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_method = "post"
        self.form_action = reverse("import:save")
        self.form_id = "trip-import-formset"
        self.layout = Layout(
            Fieldset(
                "Trip {{ forloop.counter }}",
                HTML(
                    """
                      {% if formset_form.errors %}
                        <div class="alert alert-danger"
                             style="font-size: 1rem;" role="alert">
                          Please correct the errors in this trip before importing.
                          </div>
                      {% endif %}
                    """
                ),
                Div(
                    Field("cave_name", wrapper_class="col-3"),
                    Field("cave_entrance", wrapper_class="col-3"),
                    Field("cave_exit", wrapper_class="col-3"),
                    Field("cave_region", wrapper_class="col-3"),
                    css_class="row mt-2",
                ),
                Div(
                    Field("cave_country", wrapper_class="col-3"),
                    Field("start", wrapper_class="col-3"),
                    Field("end", wrapper_class="col-3"),
                    css_class="row mt-2",
                ),
                Div(
                    Field("clubs", wrapper_class="col-3"),
                    Field("expedition", wrapper_class="col-3"),
                    Field("type", wrapper_class="col-3"),
                    Field("privacy", wrapper_class="col-3"),
                    css_class="row mt-2",
                ),
                Div(
                    Field("horizontal_dist", wrapper_class="col-2"),
                    Field("vert_dist_down", wrapper_class="col-2"),
                    Field("vert_dist_up", wrapper_class="col-2"),
                    Field("surveyed_dist", wrapper_class="col-2"),
                    Field("resurveyed_dist", wrapper_class="col-2"),
                    Field("aid_dist", wrapper_class="col-2"),
                    css_class="row mt-2",
                ),
                Div(
                    Field("cavers", wrapper_class="col-12"),
                    css_class="row mt-2",
                ),
                Div(
                    Field("notes", wrapper_class="col-12"),
                    css_class="row mt-2",
                ),
                css_class="mt-4",
            )
        )
        self.add_input(Submit("submit", "Import", css_class="mt-4"))


TripImportFormset = forms.formset_factory(
    TripImportForm, max_num=50, absolute_max=60, extra=0
)
