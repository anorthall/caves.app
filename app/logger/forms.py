from datetime import timedelta

from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Field, Fieldset, Layout, Submit
from dal import autocomplete
from django import forms
from django.core.exceptions import ValidationError
from django.urls import reverse_lazy
from django.utils import timezone
from users.models import CavingUser

from .mixins import CleanCaveLocationMixin, DistanceUnitFormMixin
from .models import Caver, Trip, TripPhoto

User = CavingUser


# noinspection PyTypeChecker
class BaseTripForm(forms.ModelForm):
    """A parent class for all forms which handle the Trip model."""

    def clean_start(self):
        """Validate the trip start date/time."""
        # Trips must not start more than a week in the future.
        one_week_from_now = timezone.now() + timedelta(days=7)
        if self.cleaned_data.get("start") > one_week_from_now:
            raise ValidationError("Trips must not start more than one week in the future.")
        return self.cleaned_data["start"]

    def clean_end(self):
        """Validate the trip end date/time."""
        # Trips must not end more than 31 days in the future.
        end = self.cleaned_data.get("end")
        if end:
            one_month_from_now = timezone.now() + timedelta(days=31)
            if end > one_month_from_now:
                raise ValidationError("Trips must not end more than 31 days in the future.")
        return end

    def clean(self):
        """Validate relations between the start/end datetimes."""
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
                self.add_error("start", "The trip start time must be before the trip end time.")
            elif length > timedelta(days=60):
                self.add_error(
                    "end",
                    "The trip is unrealistically long in duration (over 60 days).",
                )
        return self.cleaned_data


# noinspection PyTypeChecker
class TripForm(DistanceUnitFormMixin, CleanCaveLocationMixin, BaseTripForm):
    class Meta:
        model = Trip
        fields = [
            "cave_name",
            "cave_entrance",
            "cave_exit",
            "cave_region",
            "cave_country",
            "cave_location",
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
            "public_notes",
        ]
        widgets = {
            "start": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "end": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "cave_location": forms.TextInput(
                attrs={
                    "hx-post": reverse_lazy("maps:geocoding"),
                    "hx-target": "#latlong",
                    "hx-trigger": "load, keyup changed delay:500ms",
                    "hx-indicator": "",
                }
            ),
            "cavers": autocomplete.ModelSelect2Multiple("log:caver_autocomplete"),
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.has_custom_fields = False
        self.fields["notes"].label = ""
        self.fields["public_notes"].label = ""
        self.helper = FormHelper()
        self.helper.form_method = "post"

        # Initialise custom fields
        custom_fields = self._get_custom_fields()

        # Set timezone help text
        tz = timezone.get_current_timezone_name()
        self.fields["start"].help_text = f"Timezone: {tz}"
        self.fields["end"].help_text = f"Timezone: {tz}"

        # Form layout
        self.helper.layout = Layout(
            Div(
                Div("cave_name", css_class="col-12"),
                Div("cave_entrance", css_class="col-12 col-lg-6"),
                Div("cave_exit", css_class="col-12 col-lg-6"),
                Div("cave_region", css_class="col-12 col-lg-6"),
                Div("cave_country", css_class="col-12 col-lg-6"),
                Div("cave_location", css_class="col-12 col-lg-6"),
                Div(
                    HTML(
                        "{% include 'maps/_htmx_geocoding_results.html' "
                        "with lat=trip.latitude lng=trip.longitude %}"
                    ),
                    css_class=("col-12 col-lg-6 d-flex flex-column justify-content-center"),
                    id="latlong",
                ),
                css_class="row",
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
<p class="text-muted">
    The unit of measurement must be entered in the field, for
    example <code>500ft</code> or <code>150m</code>. Distances recorded are counted
    towards your overall statistics, unless they are added to a 'Surface' trip, in
    which case they will be ignored. Supported units: <code>m km cm ft yd
    inch mi furlong</code>.
</p>
                """
                ),
                HTML(
                    """
<p class="text-muted mb-4">
    <code>Surveyed distance</code> and <code>resurveyed distance</code>
    are intended to distinguish between brand new passage which has been surveyed and
    older passage which has been resurveyed. <code>Surveyed distance</code> should not
    include data which has also been entered into <code>resurveyed distance</code>.
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
                "Private notes",
                "notes",
                css_class="mt-4",
            ),
            Fieldset(
                "Public notes",
                "public_notes",
                css_class="mt-4",
            ),
        )

        if self.instance.pk:
            self.helper.add_input(Submit("submit", "Update trip", css_class="btn-lg w-100 mt-4"))
        else:
            self.helper.add_input(Submit("submit", "Create trip", css_class="btn-lg w-100 mt-4"))
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
        return None


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
    TRIP_TYPE_CHOICES = [("Any", "Any trip type")] + Trip.TRIP_TYPES

    terms = forms.CharField(
        label="Search terms",
        required=True,
        help_text="Text to search for in trip records.",
    )
    user = forms.CharField(
        label="Username",
        required=False,
        help_text="Limit search to a specific username.",
    )
    trip_type = forms.ChoiceField(
        choices=TRIP_TYPE_CHOICES, help_text="Limit search to a specific trip type."
    )
    cave_name = forms.BooleanField(initial=True, required=False)
    cave_entrance = forms.BooleanField(initial=True, required=False)
    cave_exit = forms.BooleanField(initial=True, required=False)
    region = forms.BooleanField(initial=True, required=False)
    country = forms.BooleanField(initial=False, required=False)
    cavers = forms.BooleanField(initial=True, required=False)
    clubs = forms.BooleanField(initial=False, required=False)
    expedition = forms.BooleanField(initial=False, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(
                "terms",
                css_class="row",
            ),
            Div(
                Div("user", css_class="col"),
                Div("trip_type", css_class="col"),
                css_class="row row-cols-1 row-cols-md-2",
            ),
            Div(
                Div(HTML("Search fields"), css_class="col-12"),
                css_class="row mt-4",
            ),
            Div(
                Div("cave_name", css_class="col"),
                Div("cave_entrance", css_class="col"),
                Div("cave_exit", css_class="col"),
                Div("region", css_class="col"),
                Div("country", css_class="col"),
                Div("cavers", css_class="col"),
                Div("clubs", css_class="col"),
                Div("expedition", css_class="col"),
                css_class="row row-cols-2 row-cols-lg-3 mt-3",
            ),
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


class LinkCaverForm(forms.Form):
    account = forms.ChoiceField(
        label="Account to link",
        required=True,
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self.fields["account"].choices = self._get_account_choices()
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.add_input(Submit("submit", "Save linked account"))

    def _get_account_choices(self):
        choices = []
        already_linked = []

        cavers = Caver.objects.filter(user=self.user)
        for caver in cavers:
            if caver.linked_account:
                already_linked.append(caver.linked_account)

        for friend in self.user.friends.all():
            if friend not in already_linked:
                choices.append([friend.username, f"{friend.name} -- @{friend.username}"])

        return choices

    def clean_account(self):
        account = self.cleaned_data.get("account")
        if not account:
            raise ValidationError("Please select an account.")

        try:
            account = User.objects.get(username=account)
        except User.DoesNotExist:
            raise ValidationError("Account not found.")

        if account == self.user:
            raise ValidationError("You cannot link your own account.")

        if account not in self.user.friends.all():
            raise ValidationError("You can only link accounts of your friends.")

        return account


class RenameCaverForm(forms.Form):
    name = forms.CharField(
        label="New name",
        required=True,
        help_text="The new name of this caver as it will appear on your trips.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()

    def clean_name(self):
        name = self.cleaned_data.get("name").strip()
        if len(name) < 3:
            raise ValidationError("Please enter at least three characters.")
        return name


class MergeCaverForm(forms.Form):
    caver = forms.ChoiceField(
        label="Record to merge",
        required=True,
        widget=forms.Select,
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        self.caver = kwargs.pop("caver")
        super().__init__(*args, **kwargs)
        self.fields["caver"].choices = self._get_caver_choices()
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.add_input(Submit("submit", "Merge caver"))

    def _get_caver_choices(self):
        choices = []

        cavers = Caver.objects.filter(user=self.user).exclude(pk=self.caver.pk).order_by("name")

        for caver in cavers:
            choices.append([caver.uuid, f"{caver.name}"])

        return choices

    def clean_caver(self):
        caver = self.cleaned_data.get("caver")
        if not caver or caver == self.caver:
            raise ValidationError("Please select a caver record to merge.")

        try:
            caver = Caver.objects.get(uuid=caver, user=self.user)
        except Caver.DoesNotExist:
            raise ValidationError("Caver record not found.")

        return caver
