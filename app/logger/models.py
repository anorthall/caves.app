from django.db import models
from django.conf import settings


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

    # User that added the caving trip
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    # Cave, cave region and country
    cave_name = models.CharField(max_length=100)
    cave_region = models.CharField(max_length=100)
    cave_country = models.CharField(max_length=100)

    # Trip timing and type
    trip_start = models.DateTimeField()
    trip_end = models.DateTimeField(blank=True, null=True)
    trip_type = models.CharField(
        max_length=15,
        choices=TRIP_TYPES,
        default=SPORT,
    )

    # Internal metadata
    trip_added = models.DateTimeField(auto_now_add=True)
    trip_updated = models.DateTimeField(auto_now=True)

    # Attendees and organisations
    cavers = models.CharField(max_length=200, blank=True)
    club = models.CharField(max_length=100, blank=True)
    expedition = models.CharField(max_length=100, blank=True)

    # Distances
    horizontal_distance = models.IntegerField(blank=True, null=True)
    vertical_distance_down = models.IntegerField(blank=True, null=True)
    vertical_distance_up = models.IntegerField(blank=True, null=True)
    surveyed_distance = models.IntegerField(blank=True, null=True)
    aid_climbing_distance = models.IntegerField(blank=True, null=True)

    # Notes
    notes = models.TextField(blank=True)

    def __str__(self):
        """Return the name of the cave visited."""
        return self.cave_name
