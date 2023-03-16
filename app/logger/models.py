from django.db import models
from django.urls import reverse
from django.conf import settings
from django.core.validators import MinValueValidator
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

    # Cave, cave region and country
    cave_name = models.CharField(max_length=100)
    cave_region = models.CharField(max_length=100, blank=True)
    cave_country = models.CharField(max_length=100, blank=True)

    # Trip timing and type
    start = models.DateTimeField("start time")
    end = models.DateTimeField("end time", blank=True, null=True)
    type = models.CharField(
        max_length=15,
        choices=TRIP_TYPES,
        default=SPORT,
    )

    # Internal metadata
    added = models.DateTimeField("trip added on", auto_now_add=True)
    updated = models.DateTimeField("trip last updated", auto_now=True)

    # Attendees and organisations
    cavers = models.CharField(
        max_length=200, blank=True, help_text="A list of cavers that were on this trip."
    )
    club = models.CharField(
        max_length=100,
        blank=True,
        help_text="A list of any caving clubs associated with this trip.",
    )
    expedition = models.CharField(
        max_length=100,
        blank=True,
        help_text="A list of any expeditions associated with this trip.",
    )

    # Distances
    horizontal_dist = models.IntegerField(
        "horizontal distance",
        blank=True,
        null=True,
        validators=[MinValueValidator(1)],
        help_text="Horizontal distance covered.",
    )
    vert_dist_down = models.IntegerField(
        "rope descent distance",
        blank=True,
        null=True,
        validators=[MinValueValidator(1)],
        help_text="Distance descended on rope.",
    )
    vert_dist_up = models.IntegerField(
        "rope ascent distance",
        blank=True,
        null=True,
        validators=[MinValueValidator(1)],
        help_text="Distance ascended on rope.",
    )
    surveyed_dist = models.IntegerField(
        "surveyed distance",
        blank=True,
        null=True,
        validators=[MinValueValidator(1)],
        help_text="Distance surveyed.",
    )
    aid_dist = models.IntegerField(
        "aid climbing distance",
        blank=True,
        null=True,
        validators=[MinValueValidator(1)],
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
