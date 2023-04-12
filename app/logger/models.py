import humanize
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from distance import DistanceField, DistanceUnitField
from django.utils.functional import cached_property
from django.utils.html import escape
from django.utils import timezone
from django.urls import reverse
from .validators import *
from tinymce.models import HTMLField


class Trip(models.Model):
    """Caving trip model."""

    # Trip types
    SPORT = "Sport"
    DIGGING = "Digging"
    SURVEY = "Survey"
    EXPLORATION = "Exploration"
    AID = "Aid climbing"
    PHOTO = "Photography"
    TRAINING = "Training"
    RESCUE = "Rescue"
    SCIENCE = "Science"
    HAULING = "Hauling"
    RIGGING = "Rigging"
    SURFACE = "Surface"
    OTHER = "Other"
    TRIP_TYPES = [
        (SPORT, SPORT),
        (DIGGING, DIGGING),
        (SURVEY, SURVEY),
        (EXPLORATION, EXPLORATION),
        (AID, AID),
        (PHOTO, PHOTO),
        (TRAINING, TRAINING),
        (RESCUE, RESCUE),
        (SCIENCE, SCIENCE),
        (HAULING, HAULING),
        (RIGGING, RIGGING),
        (SURFACE, SURFACE),
        (OTHER, OTHER),
    ]

    # Privacy
    DEFAULT = "Default"
    PUBLIC = "Public"
    FRIENDS = "Friends"
    PRIVATE = "Private"
    PRIVACY_CHOICES = [
        (DEFAULT, "Anyone who can view my profile"),
        (PUBLIC, "Anyone, even if my profile is private"),
        (FRIENDS, "Only my friends"),
        (PRIVATE, "Only me"),
    ]

    # User that added the caving trip
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    # Public visibility
    privacy = models.CharField(
        "Who can view this trip?",
        max_length=10,
        choices=PRIVACY_CHOICES,
        default=DEFAULT,
    )

    # Cave details
    cave_name = models.CharField(max_length=100)
    cave_region = models.CharField(max_length=100, blank=True)
    cave_country = models.CharField(max_length=100, blank=True)
    cave_url = models.URLField(
        "cave website",
        blank=True,
        help_text="A website, such as a Wikipedia page, giving more information on this cave.",
    )

    # Trip details
    start = models.DateTimeField("start time")
    end = models.DateTimeField("end time", blank=True, null=True)
    duration = models.DurationField(blank=True, null=True)
    duration_str = models.CharField(max_length=100, blank=True, null=True)
    type = models.CharField(
        max_length=15,
        choices=TRIP_TYPES,
        default=SPORT,
    )
    cavers = models.CharField(
        max_length=250, blank=True, help_text="A list of cavers that were on this trip."
    )
    clubs = models.CharField(
        max_length=100,
        blank=True,
        help_text="A list of any caving clubs associated with this trip.",
    )
    expedition = models.CharField(
        max_length=100,
        blank=True,
        help_text="A list of any expeditions associated with this trip.",
    )

    # Internal metadata
    added = models.DateTimeField("trip added on", auto_now_add=True)
    updated = models.DateTimeField("trip last updated", auto_now=True)

    # Distances
    horizontal_dist = DistanceField(
        max_digits=14,
        decimal_places=6,
        verbose_name="horizontal distance",
        unit="m",
        unit_field="horizontal_dist_units",
        blank=True,
        null=True,
        validators=[above_zero_dist_validator, horizontal_dist_validator],
        help_text="Horizontal distance covered.",
    )
    horizontal_dist_units = DistanceUnitField()

    vert_dist_down = DistanceField(
        max_digits=14,
        decimal_places=6,
        verbose_name="rope descent distance",
        unit="m",
        unit_field="vert_dist_down_units",
        blank=True,
        null=True,
        validators=[above_zero_dist_validator, vertical_dist_validator],
        help_text="Distance descended on rope.",
    )
    vert_dist_down_units = DistanceUnitField()

    vert_dist_up = DistanceField(
        max_digits=14,
        decimal_places=6,
        verbose_name="rope ascent distance",
        unit="m",
        unit_field="vert_dist_up_units",
        blank=True,
        null=True,
        validators=[above_zero_dist_validator, vertical_dist_validator],
        help_text="Distance ascended on rope.",
    )
    vert_dist_up_units = DistanceUnitField()

    surveyed_dist = DistanceField(
        max_digits=14,
        decimal_places=6,
        verbose_name="surveyed distance",
        unit="m",
        unit_field="surveyed_dist_units",
        blank=True,
        null=True,
        validators=[above_zero_dist_validator, horizontal_dist_validator],
        help_text="New passage surveyed.",
    )
    surveyed_dist_units = DistanceUnitField()

    resurveyed_dist = DistanceField(
        max_digits=14,
        decimal_places=6,
        verbose_name="resurveyed distance",
        unit="m",
        unit_field="resurveyed_dist_units",
        blank=True,
        null=True,
        validators=[above_zero_dist_validator, horizontal_dist_validator],
        help_text="Distance resurveyed.",
    )
    resurveyed_dist_units = DistanceUnitField()

    aid_dist = DistanceField(
        max_digits=14,
        decimal_places=6,
        verbose_name="aid climbing distance",
        unit="m",
        unit_field="aid_dist_units",
        blank=True,
        null=True,
        validators=[above_zero_dist_validator, vertical_dist_validator],
        help_text="Distance covered by aid climbing.",
    )
    aid_dist_units = DistanceUnitField()

    # Notes
    notes = models.TextField(blank=True)

    def __str__(self):
        """Return the name of the cave visited."""
        return self.cave_name

    def set_duration(self):
        """Sets the trip duration"""
        if self.end:
            self.duration = self.end - self.start
        else:
            self.duration = None
        return self.duration

    def set_duration_str(self):
        """Sets the human english expression of the duration"""
        td = None
        if self.end:
            td = self.end - self.start

        if td:
            self.duration_str = humanize.precisedelta(td, minimum_unit="minutes")
        else:
            self.duration_str = None
        return self.duration_str

    def save(self, *args, **kwargs):
        """Set the duration and duration_str fields"""
        self.set_duration()
        self.set_duration_str()
        return super().save(*args, **kwargs)

    def clean(self):
        """Check that the start is before the end"""
        # Check self.start exists - may have been removed by form validation
        # If it does not exist 'for real', the form/low level model validation will catch it.
        if self.start and self.end:
            if self.start > self.end:
                raise ValidationError(
                    "The trip start time must be before the trip end time."
                )

    def get_absolute_url(self):
        return reverse("log:trip_detail", kwargs={"pk": self.pk})

    @property
    def has_distances(self):
        """Return True if at least one distance measurement is recorded"""
        if self.horizontal_dist or self.vert_dist_down or self.vert_dist_up:
            return True
        elif self.aid_dist or self.surveyed_dist or self.resurveyed_dist:
            return True

    @property
    def is_private(self):
        if self.privacy == self.DEFAULT:
            return self.user.is_private
        elif self.privacy == self.PUBLIC:
            return False
        return True

    @property
    def is_public(self):
        if self.privacy == self.DEFAULT:
            return self.user.is_public
        elif self.privacy == self.PUBLIC:
            return True
        return False

    @property
    def has_report(self):
        return hasattr(self, "report") and self.report is not None

    @cached_property
    def number(self):
        """Returns the 'index' of the trip by date"""
        qs = Trip.objects.filter(user=self.user).order_by("start", "-pk")
        index = list(qs.values_list("pk", flat=True)).index(self.pk)
        return index + 1

    @cached_property
    def tidbits(self):
        """Return a dict of tidbits of information for small cards"""
        data = []
        if self.cave_region and self.cave_country:
            data.append(("Location", f"{self.cave_region} / {self.cave_country}"))

        data.extend(
            [  # Fields eligible for inclusion
                ("Clubs", self.clubs),
                ("Expedition", self.expedition),
                ("Duration", self.duration_str),
                ("Distance", self.horizontal_dist),
                ("Climbed", self.vert_dist_up),
                ("Descended", self.vert_dist_down),
                ("Surveyed", self.surveyed_dist),
                ("Resurveyed", self.resurveyed_dist),
                ("Aided", self.aid_dist),
            ]
        )

        # Remove empty values and escape HTML
        valid_data = []
        for k, v in data:
            if v:
                valid_data.append((k, escape(v)))

        return valid_data

    @cached_property
    def html_tidbits(self):
        """Return usable HTML from get_tidbits()"""
        if not self.tidbits:
            return None
        span = '<span class="text-muted">'

        if len(self.tidbits) == 1:  # Return just the one
            return f"{span}{self.tidbits[0][0]}</span> {self.tidbits[0][1]}"

        html = ""
        for k, v in self.tidbits:
            new = f" {span}{k}</span> {v}"
            html = html + new

        return html

    @cached_property
    def next_trip(self):
        """Return the next trip for the user ordered by start date"""
        qs = Trip.objects.filter(user=self.user).order_by("start", "-pk")
        index = list(qs.values_list("pk", flat=True)).index(self.pk)
        try:
            return qs[index + 1]
        except (IndexError, ValueError):
            return None

    @cached_property
    def prev_trip(self):
        """Return the previous trip ordered by start date"""
        qs = Trip.objects.filter(user=self.user).order_by("start", "-pk")
        index = list(qs.values_list("pk", flat=True)).index(self.pk)
        try:
            return qs[index - 1]
        except (IndexError, ValueError):
            return None


class TripReport(models.Model):
    class Meta:
        unique_together = ("user", "slug")

    # Relationships
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    trip = models.OneToOneField(
        Trip, on_delete=models.CASCADE, primary_key=True, related_name="report"
    )

    # Content
    title = models.CharField(max_length=100)
    pub_date = models.DateField(
        "date published", help_text="The date which will be shown on the report."
    )
    slug = models.SlugField(
        max_length=100,
        help_text="A unique identifier for the URL of the report. No spaces or special characters allowed.",
    )
    content = HTMLField()

    # Metadata
    added = models.DateTimeField("report added on", auto_now_add=True)
    updated = models.DateTimeField("report last updated", auto_now=True)

    # Privacy
    DEFAULT = "Default"
    PUBLIC = "Public"
    FRIENDS = "Friends"
    PRIVATE = "Private"
    PRIVACY_CHOICES = [
        (DEFAULT, "Anyone who can view the trip"),
        (PUBLIC, "Anyone, even if the trip is private"),
        (FRIENDS, "Only my friends"),
        (PRIVATE, "Only me"),
    ]

    privacy = models.CharField(
        "Who can view this report?",
        max_length=10,
        choices=PRIVACY_CHOICES,
        default=DEFAULT,
    )

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("log:report_detail", kwargs={"pk": self.pk})

    @property
    def is_private(self):
        if self.privacy == self.DEFAULT:
            return self.trip.is_private
        elif self.privacy == self.PUBLIC:
            return False
        return True

    @property
    def is_public(self):
        if self.is_private == False:
            return True
