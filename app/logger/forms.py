from datetime import timedelta

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone
from users.models import Notification

from .models import Comment, Trip, TripReport

User = get_user_model()


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
                    "The start and end time must not be the same. If you "
                    "do not know the end time, leave it blank.",
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


class AddCommentForm(forms.Form):
    content = forms.CharField(
        required=True,
        help_text="Your comment will be visible to anyone who can view this page.",
        widget=forms.Textarea(attrs={"rows": 4}),
    )
    type = forms.CharField(widget=forms.HiddenInput())
    pk = forms.IntegerField(widget=forms.HiddenInput())

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.request = request

        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_class = ""
        self.helper.form_show_errors = False
        self.helper.form_show_labels = False
        self.helper.form_action = reverse("log:comment_add")
        self.helper.add_input(Submit("submit", "Add comment"))

    def clean_type(self):
        type = self.cleaned_data.get("type")
        if type == "trip":
            self.type_str = "trip"
            return Trip
        elif type == "tripreport":
            self.type_str = "trip report"
            return TripReport
        else:
            raise ValidationError(
                "You are not allowed to comment on that type of item."
            )

    def clean_content(self):
        content = self.cleaned_data.get("content")
        if len(content) < 10:
            raise ValidationError("Your comment must be at least 5 characters long.")
        elif len(content) > 2000:
            raise ValidationError(
                "Your comment must be less than 2000 characters long."
            )
        return content

    def clean(self):
        cleaned_data = super().clean()
        type = cleaned_data.get("type")
        pk = cleaned_data.get("pk")

        try:
            self.object = type.objects.get(pk=pk)
        except AttributeError:
            raise ValidationError("The item you wish to comment on does not exist.")

        if not self.object.is_viewable_by(self.request.user):
            raise ValidationError("You are not allowed to comment on that item.")

        return self.cleaned_data

    def save(self, commit=True):
        content = self.cleaned_data.get("content")
        new = Comment.objects.create(
            content_object=self.object, author=self.request.user, content=content
        )
        if commit:
            new.save()
        return new
