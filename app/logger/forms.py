from django import forms
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
