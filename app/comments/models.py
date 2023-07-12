import uuid

from django.conf import settings
from django.db import models
from logger.models import Trip


class Comment(models.Model):
    content = models.TextField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="comments")

    uuid = models.UUIDField(unique=True, editable=False, default=uuid.uuid4)
    added = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-added"]

    def __str__(self):
        return f"Comment by {self.author} on {self.trip}"

    def get_absolute_url(self):
        return self.trip.get_absolute_url()
