from django import forms
from django.core.exceptions import ValidationError
from .models import Trip


class TripForm(forms.ModelForm):
    template_name = "forms/trip_form.html"

    class Meta:
        model = Trip
        exclude = ["user", "privacy"]
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
