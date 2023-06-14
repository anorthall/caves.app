from django.conf import settings
from django.db import models
from django.urls import reverse
from tinymce.models import HTMLField

from .trip import Trip


# noinspection PyUnresolvedReferences
class TripReport(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "slug"], name="unique_slug_per_user"
            )
        ]

    # Relationships
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    trip = models.OneToOneField(
        Trip, on_delete=models.CASCADE, primary_key=True, related_name="report"
    )
    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="liked_reports"
    )

    # Content
    title = models.CharField(max_length=100)
    pub_date = models.DateField(
        "date published", help_text="The date which will be shown on the report."
    )
    slug = models.SlugField(
        max_length=100,
        help_text=(
            "A unique identifier for the URL of the report. "
            "No spaces or special characters allowed."
        ),
    )
    content = HTMLField()

    # Metadata
    added = models.DateTimeField("report added on", auto_now_add=True)
    updated = models.DateTimeField("report last updated", auto_now=True)

    # Privacy
    DEFAULT = "Default"
    PUBLIC = "Public"
    FRIENDS = "Friends"
    PRIVATE = "Private"
    PRIVACY_CHOICES = [
        (DEFAULT, "Anyone who can view the trip"),
        (PUBLIC, "Anyone, even if the trip is private"),
        (FRIENDS, "Only my friends"),
        (PRIVATE, "Only me"),
    ]

    privacy = models.CharField(
        "Who can view this report?",
        max_length=10,
        choices=PRIVACY_CHOICES,
        default=DEFAULT,
    )

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("log:report_detail", args=[self.trip.uuid])

    def is_viewable_by(self, user_viewing):
        """Returns whether or not user_viewing can view this report"""
        if user_viewing == self.user:
            return True

        if self.privacy == self.PUBLIC:
            return True

        if self.privacy == self.FRIENDS:
            if user_viewing in self.user.friends.all():
                return True

        if self.privacy == self.DEFAULT:
            return self.trip.is_viewable_by(user_viewing)

        return False

    @property
    def is_private(self):
        if self.privacy == self.DEFAULT:
            return self.trip.is_private
        elif self.privacy == self.PUBLIC:
            return False
        return True

    @property
    def is_public(self):
        if self.is_private is False:
            return True
