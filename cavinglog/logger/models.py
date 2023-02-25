from django.db import models
from django.conf import settings


class CavingTrip(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    cave_name = models.CharField(max_length=100)
    cave_region = models.CharField(max_length=100)
    cave_country = models.CharField(max_length=100)

    trip_start = models.DateTimeField()
    trip_end = models.DateTimeField(blank=True)
    trip_type = models.CharField(max_length=15)
    trip_added = models.DateTimeField(auto_now_add=True)
    trip_updated = models.DateTimeField(auto_now=True)

    cavers = models.TextField(blank=True)
    club = models.CharField(max_length=100, blank=True)
    expedition = models.CharField(max_length=100, blank=True)

    horizontal_distance = models.IntegerField(blank=True)
    vertical_distance_down = models.IntegerField(blank=True)
    vertical_distance_up = models.IntegerField(blank=True)
    surveyed_distance = models.IntegerField(blank=True)

    notes = models.TextField(blank=True)
