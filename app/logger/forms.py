from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
from social.models import Notification
from .models import Trip, TripReport


class TripReportForm(forms.ModelForm):
    template_name = "forms/tripreport_form.html"

    class Meta:
        model = TripReport
        exclude = ["user", "trip"]
        widgets = {
            "pub_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        """Store the trip user. This is used to validate the slug."""
        self.user = kwargs.pop("user")
        return super().__init__(*args, **kwargs)

    def clean_slug(self):
        """Check that the user does not have another slug with the same value"""
        slug = self.cleaned_data.get("slug")
        try:
            tr = TripReport.objects.get(user=self.user, slug=slug)
            if tr == self.instance:
                return slug
            raise ValidationError("The slug must be unique.")
        except TripReport.DoesNotExist:
            return slug


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
        end = self.cleaned_data.get("end")
        if end:
            one_month_from_now = timezone.now() + timedelta(days=31)
            if end > one_month_from_now:
                raise ValidationError(
                    "Trips must not end more than 31 days in the future."
                )
        return end

    def clean(self):
        """Validate relations between the start/end datetimes"""
        super().clean()

        start = self.cleaned_data.get("start")
        end = self.cleaned_data.get("end")

        if end and start:
            length = end - start
            if end == start:
                self.add_error(
                    "end",
                    "The start and end time must not be the same. If you do not know the end time, leave it blank.",
                )
            elif start > end:
                self.add_error(
                    "start", "The trip start time must be before the trip end time."
                )
            elif length > timedelta(days=60):
                self.add_error(
                    "end",
                    "The trip is unrealistically long in duration (over 60 days).",
                )


class AllUserNotificationForm(forms.ModelForm):
    """Form to send a notification to all users"""

    template_name = "forms/bs5_form.html"

    class Meta:
        model = Notification
        fields = ["message", "url"]
