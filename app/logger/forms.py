from datetime import timedelta

from crispy_bootstrap5.bootstrap5 import FloatingField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Field, Fieldset, Layout, Submit
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone

from .mixins import DistanceUnitFormMixin
from .models import Trip, TripPhoto, TripReport

User = get_user_model()


# noinspection PyTypeChecker
class TripReportForm(forms.ModelForm):
    class Meta:
        model = TripReport
        fields = [
            "title",
            "pub_date",
            "slug",
            "content",
            "privacy",
        ]
        widgets = {
            "pub_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields["content"].label = ""
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Fieldset(
                "Report",
                FloatingField("title"),
                Div(
                    Div("pub_date", css_class="col-12 col-xl-6"),
                    Div("slug", css_class="col-12 col-xl-6"),
                    css_class="row mt-4",
                ),
                css_class="mt-4",
            ),
            Fieldset(
                "Content",
                "content",
                css_class="mt-4",
            ),
            Fieldset(
                "Privacy",
                "privacy",
                css_class="mt-4",
            ),
        )

        if self.instance.pk:
            self.helper.add_input(
                Submit("submit", "Update report", css_class="btn-lg w-100 mt-4")
            )
        else:
            self.helper.add_input(
                Submit("submit", "Create report", css_class="btn-lg w-100 mt-4")
            )

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


# noinspection PyTypeChecker
class TripForm(DistanceUnitFormMixin, forms.ModelForm):
    class Meta:
        model = Trip
        fields = [
            "cave_name",
            "cave_entrance",
            "cave_exit",
            "cave_region",
            "cave_country",
            "cave_url",
            "start",
            "end",
            "type",
            "privacy",
            "clubs",
            "expedition",
            "cavers",
            "horizontal_dist",
            "vert_dist_down",
            "vert_dist_up",
            "surveyed_dist",
            "resurveyed_dist",
            "aid_dist",
            "notes",
            "custom_field_1",
            "custom_field_2",
            "custom_field_3",
            "custom_field_4",
            "custom_field_5",
        ]
        widgets = {
            "start": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "end": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.has_custom_fields = False
        self.fields["notes"].label = ""
        self.helper = FormHelper()
        self.helper.form_method = "post"
        custom_fields = self._get_custom_fields()
        self.helper.layout = Layout(
            Fieldset(
                "Cave details",
                Div(
                    Div("cave_name", css_class="col-12"),
                    Div("cave_entrance", css_class="col-12 col-lg-6"),
                    Div("cave_exit", css_class="col-12 col-lg-6"),
                    Div("cave_region", css_class="col-12 col-lg-6"),
                    Div("cave_country", css_class="col-12 col-lg-6"),
                    Div("cave_url", css_class="col-12"),
                    css_class="row",
                ),
            ),
            Fieldset(
                "Trip details",
                Div(
                    Div("start", css_class="col-12 col-lg-6"),
                    Div("end", css_class="col-12 col-lg-6"),
                    Div("type", css_class="col-12 col-lg-6"),
                    Div("privacy", css_class="col-12 col-lg-6"),
                    Div("clubs", css_class="col-12 col-lg-6"),
                    Div("expedition", css_class="col-12 col-lg-6"),
                    Div("cavers", css_class="col"),
                    css_class="row",
                ),
                css_class="mt-4",
            ),
            custom_fields,
            Fieldset(
                "Distances",
                HTML(
                    """
<p class="text-muted mb-4">
    The unit of measurement must be entered in the field, for
    example <code>500ft</code> or <code>150m</code>. Distances recorded are counted
    towards your overall statistics, unless they are added to a 'Surface' trip, in
    which case they will be ignored. Supported units: <code>m km cm ft yd
    inch mi furlong</code>.
</p>
                """
                ),
                Div(
                    Div("horizontal_dist", css_class="col"),
                    Div("vert_dist_down", css_class="col"),
                    Div("vert_dist_up", css_class="col"),
                    Div("surveyed_dist", css_class="col"),
                    Div("resurveyed_dist", css_class="col"),
                    Div("aid_dist", css_class="col"),
                    css_class="row row-cols-1 row-cols-lg-3",
                ),
                css_class="mt-4",
            ),
            Fieldset(
                "Trip notes",
                "notes",
                css_class="mt-4",
            ),
        )

        if self.instance.pk:
            self.helper.add_input(
                Submit("submit", "Update trip", css_class="btn-lg w-100 mt-4")
            )
        else:
            self.helper.add_input(
                Submit("submit", "Create trip", css_class="btn-lg w-100 mt-4")
            )
            self.helper.add_input(
                Submit(
                    "addanother",
                    "Create and add another",
                    css_class="btn-secondary btn-lg w-100 mt-3",
                )
            )

    def _get_custom_fields(self):
        valid_field_names = []
        invalid_field_names = []
        for field_name, field in self.fields.items():
            if not field_name.startswith("custom_field_"):
                continue

            label = getattr(self.user, f"{field_name}_label")
            if label:
                field.label = label
                valid_field_names.append(field_name)
            else:
                invalid_field_names.append(field_name)

        for field_name in invalid_field_names:
            del self.fields[field_name]

        if valid_field_names:
            custom_fields = Layout(
                Fieldset(
                    "Custom fields",
                    Div(
                        css_class="row row-cols-1 row-cols-lg-2",
                    ),
                    css_class="mt-4",
                )
            )

            for field_name in valid_field_names:
                custom_fields[0][0].append(
                    Div(Field(field_name), css_class="col"),
                )
            return custom_fields
        else:
            return None

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


class TripPhotoForm(forms.ModelForm):
    class Meta:
        model = TripPhoto
        fields = ("caption",)


class PhotoPrivacyForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = ("private_photos",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.add_input(Submit("submit", "Save privacy setting"))


class TripSearchForm(forms.Form):
    terms = forms.CharField(
        label="Terms",
        required=True,
        help_text="Text to search for in trip records.",
    )
    user = forms.CharField(
        label="Username",
        required=False,
        help_text="Limit search to a specific user (optional).",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "get"
        self.helper.form_action = reverse("log:search_results")
        self.helper.layout = Layout(
            Div(
                Field("terms", wrapper_class="col-12 col-lg-8"),
                Field("user", wrapper_class="col-12 col-lg-4"),
                css_class="row",
            ),
            Submit("submit", "Search", css_class="btn btn-primary w-100 mt-3"),
        )

    def clean_terms(self):
        terms = self.cleaned_data.get("terms").strip()
        if len(terms) < 3:
            raise ValidationError("Please enter at least three characters.")
        return terms

    def clean_user(self):
        user = self.cleaned_data.get("user").strip()
        if user:
            try:
                user = User.objects.get(username=user)
            except User.DoesNotExist:
                raise ValidationError("Username not found.")
        return user
