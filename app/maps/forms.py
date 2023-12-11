from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Fieldset, Layout, Submit
from django import forms
from django.urls import reverse_lazy
from django.utils.html import escape
from django.utils.safestring import SafeString
from logger.mixins import CleanCaveLocationMixin
from logger.models import Trip


class BulkLocationForm(forms.ModelForm, CleanCaveLocationMixin):
    additional_caves = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        label="",
        required=False,
    )

    class Meta:
        model = Trip
        fields = ["cave_location"]
        widgets = {
            "cave_location": forms.TextInput(
                attrs={
                    "hx-post": reverse_lazy("maps:geocoding"),
                    "hx-target": "#latlong",
                    "hx-trigger": "load, keyup changed delay:500ms",
                    "hx-indicator": "",
                }
            ),
        }

    def __init__(self, trip, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.trip = trip
        self.helper = FormHelper()

        similar_caves = []
        cave_name = self.trip.cave_name.strip().lower()
        entrance = self.trip.cave_entrance.strip().lower()
        for other_trip in self.trip.user.trips.exclude(id=self.trip.id):
            if other_trip.cave_coordinates:
                continue
            if cave_name == other_trip.cave_name.strip().lower():
                similar_caves.append(other_trip)
            elif other_trip.cave_entrance and entrance:
                if entrance == other_trip.cave_entrance.strip().lower():
                    similar_caves.append(other_trip)

        if similar_caves:
            choices = []
            for trip in similar_caves:
                # Escape the cave name and entrance and then mark the label as safe
                # after inserting the link to the trip.
                date = trip.start.strftime("%Y-%m-%d")
                label = f"Trip to { escape(trip.cave_name) } on {date}"
                if trip.cave_entrance:
                    label += f" via { escape(trip.cave_entrance) }"
                label += f" &mdash; <a href='{ trip.get_absolute_url() }'>View</a>"

                choices.append((trip.uuid, SafeString(label)))

            self.fields["additional_caves"].choices = choices
            self.fields["additional_caves"].initial = [
                trip.uuid for trip in similar_caves
            ]
        else:
            del self.fields["additional_caves"]

        self.helper.layout = Layout(
            Div(
                Div("cave_location", css_class="col-12 col-lg-6"),
                Div(
                    HTML(
                        "{% include 'maps/_htmx_geocoding_results.html' "
                        "with lat=trip.latitude lng=trip.longitude %}"
                    ),
                    css_class=(
                        "col-12 col-lg-6 d-flex flex-column justify-content-center"
                    ),
                    id="latlong",
                ),
                css_class="row",
            ),
        )

        if similar_caves:
            self.helper.layout.append(
                Fieldset(
                    "Similar caves",
                    HTML(
                        """
<p class="text-muted">
    The following trips have the same cave name and/or cave entrance as this trip. If
    you would like to add the same location to these trips, check the box next to the
    trip name and all selected trips will be updated with the location you entered
    above.
</p>
                    """
                    ),
                    "additional_caves",
                    css_class="mt-5",
                ),
            )

        self.helper.add_input(
            Submit("submit", "Save trip location(s)", css_class="btn btn-primary mt-3")
        )

    def clean_additional_caves(self):
        caves = self.cleaned_data["additional_caves"]
        return caves if not caves else self.trip.user.trips.filter(uuid__in=caves)
