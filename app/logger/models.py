from django.db import models
from django.urls import reverse
from django.utils.html import escape
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
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
    horizontal_dist = models.IntegerField(
        "horizontal distance",
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(20000)],
        help_text="Horizontal distance covered.",
    )
    vert_dist_down = models.IntegerField(
        "rope descent distance",
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(5000)],
        help_text="Distance descended on rope.",
    )
    vert_dist_up = models.IntegerField(
        "rope ascent distance",
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(5000)],
        help_text="Distance ascended on rope.",
    )
    surveyed_dist = models.IntegerField(
        "surveyed distance",
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(20000)],
        help_text="Distance surveyed.",
    )
    aid_dist = models.IntegerField(
        "aid climbing distance",
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(1000)],
        help_text="Distance covered by aid climbing.",
    )

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

    def duration(self):
        """Return a the trip duration or None"""
        if not self.end:
            return None
        return self.end - self.start

    def duration_str(self):
        """Return a human english expression of the duration"""
        td = self.duration()
        if td is None:
            return None

        return humanize.precisedelta(td, minimum_unit="minutes")

    def has_distances(self):
        """Return True if at least one distance measurement is recorded"""
        if self.horizontal_dist or self.vert_dist_down or self.vert_dist_up:
            return True
        elif self.aid_dist or self.surveyed_dist:
            return True

    def is_private(self):
        if self.privacy == self.DEFAULT:
            return self.user.is_private()
        elif self.privacy == self.PUBLIC:
            return False
        return True

    def is_public(self):
        if self.privacy == self.DEFAULT:
            return self.user.is_public()
        elif self.privacy == self.PUBLIC:
            return True
        return False

    def number(self):
        """Returns the 'index' of the trip by date"""
        qs = Trip.objects.filter(user=self.user).order_by("start")
        index = list(qs.values_list("pk", flat=True)).index(self.pk)
        return index + 1

    def get_tidbits(self, num_items=4, escape_html=True):
        """Return a dict of tidbits of information for small cards"""
        data = []
        if self.cave_region and self.cave_country:
            data.append(("Location", f"{self.cave_region} / {self.cave_country}"))

        data.extend(
            [  # Fields eligible for inclusion
                ("Clubs", self.clubs),
                ("Expedition", self.expedition),
                ("Duration", self.duration_str()),
                ("Distance", self.horizontal_dist),
                ("Climbed", self.vert_dist_up),
                ("Descended", self.vert_dist_down),
                ("Surveyed", self.surveyed_dist),
                ("Aided", self.aid_dist),
            ]
        )
        valid_data = []
        for k, v in data:  # Remove empty values
            if v:
                if escape_html:
                    valid_data.append((k, escape(v)))
                else:
                    valid_data.append((k, v))
        return valid_data[:num_items]

    def get_html_tidbits(self, **kwargs):
        """Return usable HTML from get_tidbits()"""
        tidbits = self.get_tidbits(**kwargs)
        if not tidbits:
            return None

        span = '<span class="text-muted">'
        if len(tidbits) == 1:
            return f"{span}{tidbits[0][0]}</span> {tidbits[0][1]}"

        html = ""
        for k, v in tidbits:
            new = f" &middot; {span}{k}</span> {v}"
            html = html + new
        html = html[10:]  # Remove first &middot;

        return html
