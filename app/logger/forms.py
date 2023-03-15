from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
from .models import Trip


class TripForm(forms.ModelForm):
    template_name = "forms/trip_form.html"

    class Meta:
        model = Trip
        exclude = ["user"]
        widgets = {
            "start": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "end": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def clean_start(self):
        """Validate the trip start date/time"""
        # Trips must not start more than a week in the future.
        one_week_from_now = timezone.now() + timedelta(days=7)
        if self.cleaned_data.get("start") > one_week_from_now:
            raise ValidationError(
                "Trips must not start more than one week in the future."
            )
        return self.cleaned_data["start"]

    def clean_end(self):
        """Validate the trip end date/time"""
        # Trips must not end more than 31 days in the future.
        one_month_from_now = timezone.now() + timedelta(days=31)
        if self.cleaned_data.get("end") > one_month_from_now:
            raise ValidationError("Trips must not end more than 31 days in the future.")
        return self.cleaned_data["end"]

    def clean(self):
        """Validate relations between the start/end datetimes"""
        super().clean()

        start = self.cleaned_data.get("start")
        end = self.cleaned_data.get("end")

        if end and start:
            # Ensure the start time is before the end time
            if start > end:
                self.add_error(
                    "start", "The trip start time must be before the trip end time."
                )

            # Check the trip is not unrealistically long
            length = end - start
            if length > timedelta(days=60):
                self.add_error(
                    "end",
                    "The trip is unrealistically long in duration (over 60 days).",
                )
