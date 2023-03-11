from django import forms
from django.core.exceptions import ValidationError
from .models import Trip


class TripForm(forms.ModelForm):
    template_name = "forms/bs5_form.html"

    class Meta:
        model = Trip
        exclude = ["user"]
        widgets = {
            "trip_start": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "trip_end": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def clean_trip_end(self):
        start = self.cleaned_data["trip_start"]
        end = self.cleaned_data["trip_end"]
        if end:
            if start > end:
                raise ValidationError(
                    "The trip start time must be before the trip end time."
                )
