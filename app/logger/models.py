from django.db import models
from django.urls import reverse
from django.utils.html import escape
from django.conf import settings
from django.utils import timezone
from django.utils.functional import cached_property
from django.core.exceptions import ValidationError
from distance import DistanceField, DistanceUnitField
from .validators import *
from django.contrib.gis.measure import Distance
import humanize


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
    TRIP_TYPES = [
        (SPORT, SPORT),
        (DIGGING, DIGGING),
        (SURVEY, SURVEY),
        (EXPLORATION, EXPLORATION),
        (AID, AID),
        (PHOTO, PHOTO),
        (TRAINING, TRAINING),
        (RESCUE, RESCUE),
    ]

    # Trip privacy types
    DEFAULT = "Default"
    PUBLIC = "Public"
    PRIVATE = "Private"
    TRIP_PRIVACY_TYPES = [
        (DEFAULT, DEFAULT),
        (PUBLIC, PUBLIC),
        (PRIVATE, PRIVATE),
    ]

    # User that added the caving trip
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    # Public visibility
    privacy = models.CharField(
        "Privacy settings",
        max_length=10,
        choices=TRIP_PRIVACY_TYPES,
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
    type = models.CharField(
        max_length=15,
        choices=TRIP_TYPES,
        default=SPORT,
    )
    cavers = models.CharField(
        max_length=200, blank=True, help_text="A list of cavers that were on this trip."
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
    report_url = models.URLField(
        "trip report",
        blank=True,
        help_text="The URL of an externally hosted trip report, such as on an expedition website or a personal blog.",
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
        help_text="Distance surveyed.",
    )
    surveyed_dist_units = DistanceUnitField()

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

    @classmethod
    def trip_index(cls, user):
        """Build a dict of a user's trips with their 'date index' mapped to the trip pk"""
        qs = cls.objects.filter(user=user).order_by("start")
        trip_list = list(qs.values_list("pk", flat=True))
        index = {}
        for trip in qs:
            index[trip.pk] = trip_list.index(trip.pk) + 1
        return index

    @classmethod
    def stats_for_user(cls, user, year=None):
        """Get statistics of Trips for a user, optionally by year"""
        # Get the QuerySet.
        qs = Trip.objects.filter(user=user)
        if year:
            qs = qs.filter(start__year=year)

        # Initialise results
        results = {
            "vert_down": Distance(m=0),
            "vert_up": Distance(m=0),
            "surveyed": Distance(m=0),
            "aided": Distance(m=0),
            "horizontal": Distance(m=0),
            "trips": 0,
            "time": timezone.timedelta(0),
        }

        # Return the empty results if there are no trips.
        if not qs:
            results["time"] = "0"
            return results

        # Iterate and add up
        for trip in qs:
            results["trips"] += 1
            results["time"] += trip.duration if trip.end else timezone.timedelta(0)
            results["vert_down"] += trip.vert_dist_down
            results["vert_up"] += trip.vert_dist_up
            results["surveyed"] += trip.surveyed_dist
            results["horizontal"] += trip.horizontal_dist
            results["aided"] += trip.aid_dist

        # Humanise duration
        results["time"] = humanize.precisedelta(
            results["time"], minimum_unit="hours", format="%.0f"
        )

        return results

    def __str__(self):
        """Return the name of the cave visited."""
        return self.cave_name

    def clean(self):
        """Check that the start is before the end"""
        if self.end:
            if self.start > self.end:
                raise ValidationError(
                    "The trip start time must be before the trip end time."
                )

    def get_absolute_url(self):
        return reverse("log:trip_detail", kwargs={"pk": self.pk})

    @cached_property
    def duration(self):
        """Return a the trip duration or None"""
        if not self.end:
            return None
        return self.end - self.start

    @cached_property
    def duration_str(self):
        """Return a human english expression of the duration"""
        td = self.duration
        if td is None:
            return ""

        return humanize.precisedelta(td, minimum_unit="minutes")

    @property
    def has_distances(self):
        """Return True if at least one distance measurement is recorded"""
        if self.horizontal_dist or self.vert_dist_down or self.vert_dist_up:
            return True
        elif self.aid_dist or self.surveyed_dist:
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

    @cached_property
    def number(self):
        """Returns the 'index' of the trip by date"""
        qs = Trip.objects.filter(user=self.user).order_by("start")
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
