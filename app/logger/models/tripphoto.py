import os
import uuid

from django.conf import settings
from django.core.files.storage import storages
from django.db import models
from imagekit.cachefiles import ImageCacheFile
from imagekit.models import ImageSpecField
from pilkit.processors import Thumbnail, Transpose

from .trip import Trip


def trip_photo_upload_path(instance, filename):
    """Returns the path to upload trip photos to"""
    original_filename, ext = os.path.splitext(filename)
    return f"p/{instance.user.uuid}/{instance.trip.uuid}/{instance.uuid}{ext}"


class TripPhoto(models.Model):
    uuid = models.UUIDField("UUID", default=uuid.uuid4, unique=True)
    trip = models.ForeignKey(Trip, related_name="photos", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    photo = models.ImageField(
        storage=storages["photos"],
        upload_to=trip_photo_upload_path,
        blank=True,
        null=True,
        max_length=150,
    )
    thumbnail = ImageSpecField(
        source="photo",
        processors=[Transpose(), Thumbnail(width=200, height=300, crop="center")],
        format="JPEG",
        options={"quality": 60},
    )
    caption = models.CharField(max_length=100, blank=True)
    is_valid = models.BooleanField(default=False)
    taken = models.DateTimeField(blank=True, null=True)
    added = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Photo for {self.trip} by {self.user}"

    def save(self, *args, **kwargs):
        """Generate thumbnails on save"""
        super().save(*args, **kwargs)
        if self.is_valid:
            for attr in dir(self):
                try:
                    val = getattr(self, attr)
                    if isinstance(val, ImageCacheFile):
                        val.generate(force=True)
                except:  # noqa E722
                    pass  # We -really- don't care if this fails.

    def get_absolute_url(self):
        return self.photo.url

    @property
    def url(self):
        return self.photo.url
