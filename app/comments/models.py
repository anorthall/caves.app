import uuid

from core.models import News
from django.conf import settings
from django.db import models
from logger.models import Trip


class BaseComment(models.Model):
    content = models.TextField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    uuid = models.UUIDField(unique=True, editable=False, default=uuid.uuid4)
    added = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Comment(BaseComment):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="comments")

    class Meta:
        ordering = ["-added"]
        verbose_name_plural = "trip comments"

    def __str__(self):
        return f"Comment by {self.author} on {self.trip}"

    def get_absolute_url(self):
        return self.trip.get_absolute_url()


class NewsComment(BaseComment):
    news = models.ForeignKey(News, on_delete=models.CASCADE, related_name="comments")

    class Meta:
        ordering = ["-added"]
        verbose_name_plural = "news comments"

    def __str__(self):
        return f"Comment by {self.author} on {self.article.title}"

    def get_absolute_url(self):
        return self.article.get_absolute_url()
