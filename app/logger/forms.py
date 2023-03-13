from django import forms
from django.core.exceptions import ValidationError
from .models import Trip


class TripForm(forms.ModelForm):
    template_name = "forms/trip_form.html"

    class Meta:
        model = Trip
        fields = [
            "start",
            "end",
            "type",
            "cave_name",
            "cave_region",
            "cave_country",
            "cavers",
            "club",
            "expedition",
            "horizontal_dist",
            "vert_dist_down",
            "vert_dist_up",
            "surveyed_dist",
            "aid_dist",
            "notes",
        ]

        widgets = {
            "start": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "end": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def clean_end(self):
        start = self.cleaned_data["start"]
        end = self.cleaned_data["end"]
        if end:
            if start > end:
                raise ValidationError(
                    "The trip start time must be before the trip end time."
                )
        return end
