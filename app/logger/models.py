from django.db import models
from django.urls import reverse
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
