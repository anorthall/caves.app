import os
import uuid

from django.conf import settings
from django.core.files.storage import storages
from django.db import models

from .trip import Trip


class TripPhotoManager(models.Manager):
    def invalid(self):
        return self.filter(is_valid=False, deleted_at=None)

    def valid(self):
        return self.filter(is_valid=True, deleted_at=None)

    def deleted(self):
        return self.filter(deleted_at__isnull=False)


def trip_photo_upload_path(instance, filename):
    """Returns the path to upload trip photos to"""
    original_filename, ext = os.path.splitext(filename)
    return f"{instance.user.uuid}/{instance.trip.uuid}/{instance.uuid}{ext}"


class TripPhoto(models.Model):
    objects = TripPhotoManager()

    uuid = models.UUIDField("UUID", default=uuid.uuid4, unique=True)
    trip = models.ForeignKey(
        Trip, related_name="photos", on_delete=models.SET_NULL, null=True
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    photo = models.ImageField(
        storage=storages["photos"],
        upload_to=trip_photo_upload_path,
        blank=True,
        null=True,
        max_length=150,
    )
    caption = models.CharField(max_length=100, blank=True)
    is_valid = models.BooleanField(default=False)
    taken = models.DateTimeField(blank=True, null=True)
    added = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    filesize = models.IntegerField(default=0)

    def __str__(self):
        return f"Photo for {self.trip} by {self.user}"

    def save(self, *args, **kwargs):
        """If the photo is deleted, remove it from the featured photo field of
        any trips it is associated with."""
        if self.deleted_at is not None or self.is_valid is False:
            for trip in self.trips_featured.all():
                trip.featured_photo = None
                trip.save()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return self.photo.url

    @property
    def url(self):
        return self.photo.url
