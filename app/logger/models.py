import humanize
from distance import D, DistanceField, DistanceUnitField
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from tinymce.models import HTMLField

from .validators import (
    above_zero_dist_validator,
    horizontal_dist_validator,
    vertical_dist_validator,
)


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
    SCIENCE = "Science"
    HAULING = "Hauling"
    RIGGING = "Rigging"
    SURFACE = "Surface"
    OTHER = "Other"
    TRIP_TYPES = [
        (SPORT, SPORT),
        (DIGGING, DIGGING),
        (SURVEY, SURVEY),
        (EXPLORATION, EXPLORATION),
        (AID, AID),
        (PHOTO, PHOTO),
        (TRAINING, TRAINING),
        (RESCUE, RESCUE),
        (SCIENCE, SCIENCE),
        (HAULING, HAULING),
        (RIGGING, RIGGING),
        (SURFACE, SURFACE),
        (OTHER, OTHER),
    ]

    # Privacy
    DEFAULT = "Default"
    PUBLIC = "Public"
    FRIENDS = "Friends"
    PRIVATE = "Private"
    PRIVACY_CHOICES = [
        (DEFAULT, "Anyone who can view my profile"),
        (PUBLIC, "Anyone, even if my profile is private"),
        (FRIENDS, "Only my friends"),
        (PRIVATE, "Only me"),
    ]

    # Cave details
    cave_name = models.CharField(max_length=100)
    cave_region = models.CharField(max_length=100, blank=True)
    cave_country = models.CharField(max_length=100, blank=True)
    cave_url = models.URLField(
        "cave website",
        blank=True,
        help_text=(
            "A website, such as a Wikipedia page, "
            "giving more information on this cave."
        ),
    )

    # Trip details
    start = models.DateTimeField("start time")
    end = models.DateTimeField("end time", blank=True, null=True)
    duration = models.DurationField(blank=True, null=True)
    duration_str = models.CharField(max_length=100, blank=True, null=True)
    type = models.CharField(
        max_length=15,
        choices=TRIP_TYPES,
        default=SPORT,
    )
    cavers = models.CharField(
        max_length=250,
        blank=True,
        help_text="A comma-separated list of cavers that were on this trip.",
    )
    clubs = models.CharField(
        max_length=100,
        blank=True,
        help_text=(
            "A comma-separated list of any caving " "clubs associated with this trip."
        ),
    )
    expedition = models.CharField(
        max_length=100,
        blank=True,
        help_text=(
            "A comma-separated list of any expeditions " "associated with this trip."
        ),
    )
    horizontal_dist = DistanceField(
        max_digits=14,
        decimal_places=6,
        verbose_name="horizontal distance",
        unit="m",
        unit_field="horizontal_dist_units",
        blank=True,
        null=True,
        validators=[above_zero_dist_validator, horizontal_dist_validator],
        help_text="Horizontal distance covered.",
    )
    horizontal_dist_units = DistanceUnitField()

    vert_dist_down = DistanceField(
        max_digits=14,
        decimal_places=6,
        verbose_name="rope descent distance",
        unit="m",
        unit_field="vert_dist_down_units",
        blank=True,
        null=True,
        validators=[above_zero_dist_validator, vertical_dist_validator],
        help_text="Distance descended on rope.",
    )
    vert_dist_down_units = DistanceUnitField()

    vert_dist_up = DistanceField(
        max_digits=14,
        decimal_places=6,
        verbose_name="rope ascent distance",
        unit="m",
        unit_field="vert_dist_up_units",
        blank=True,
        null=True,
        validators=[above_zero_dist_validator, vertical_dist_validator],
        help_text="Distance ascended on rope.",
    )
    vert_dist_up_units = DistanceUnitField()

    surveyed_dist = DistanceField(
        max_digits=14,
        decimal_places=6,
        verbose_name="surveyed distance",
        unit="m",
        unit_field="surveyed_dist_units",
        blank=True,
        null=True,
        validators=[above_zero_dist_validator, horizontal_dist_validator],
        help_text="New passage surveyed.",
    )
    surveyed_dist_units = DistanceUnitField()

    resurveyed_dist = DistanceField(
        max_digits=14,
        decimal_places=6,
        verbose_name="resurveyed distance",
        unit="m",
        unit_field="resurveyed_dist_units",
        blank=True,
        null=True,
        validators=[above_zero_dist_validator, horizontal_dist_validator],
        help_text="Distance resurveyed.",
    )
    resurveyed_dist_units = DistanceUnitField()

    aid_dist = DistanceField(
        max_digits=14,
        decimal_places=6,
        verbose_name="aid climbing distance",
        unit="m",
        unit_field="aid_dist_units",
        blank=True,
        null=True,
        validators=[above_zero_dist_validator, vertical_dist_validator],
        help_text="Distance covered by aid climbing.",
    )
    aid_dist_units = DistanceUnitField()

    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="liked_trips"
    )
    privacy = models.CharField(
        "Who can view this trip?",
        max_length=10,
        choices=PRIVACY_CHOICES,
        default=DEFAULT,
    )
    notes = models.TextField(blank=True)
    added = models.DateTimeField("trip added on", auto_now_add=True)
    updated = models.DateTimeField("trip last updated", auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.cave_name

    def _set_duration(self):
        """Store the duration in the database as a timedelta"""
        if self.end:
            self.duration = self.end - self.start
        else:
            self.duration = None
        return self.duration

    def _set_duration_str(self):
        """Store the duration in the database as a string"""
        td = None
        if self.end:
            td = self.end - self.start

        if td:
            self.duration_str = humanize.precisedelta(
                td, minimum_unit="minutes", suppress=["days", "months", "years"]
            )
        else:
            self.duration_str = None
        return self.duration_str

    def save(self, *args, **kwargs):
        self._set_duration()
        self._set_duration_str()

        # Distance fields should be set to None instead of
        # '0m', '0ft' etc if they are zero. This is because
        # sorting does not work properly unless they are None.
        # I suspect this is a bug in django-distance-field?
        for field in self._meta.fields:
            if isinstance(field, DistanceField):
                if getattr(self, field.name) == 0:
                    setattr(self, field.name, None)

        return super().save(*args, **kwargs)

    def clean(self):
        # Check self.start exists - may have been removed by form validation
        # If it does not exist 'for real', the form/low level model validation
        # will catch it.
        if self.start and self.end:
            if self.start > self.end:
                raise ValidationError(
                    "The trip start time must be before the trip end time."
                )

    def get_absolute_url(self):
        return reverse("log:trip_detail", kwargs={"pk": self.pk})

    def sanitise(self, user_viewing):
        """Sanitise the trip for viewing by another user"""
        if user_viewing != self.user and self.user.private_notes is True:
            self.notes = None
        return self

    def is_viewable_by(self, user_viewing):
        """Returns whether or not user_viewing can view this trip"""
        if user_viewing == self.user:
            return True

        if self.privacy == self.PUBLIC:
            return True

        if self.privacy == self.FRIENDS:
            if user_viewing in self.user.friends.all():
                return True

        if self.privacy == self.DEFAULT:
            return self.user.is_viewable_by(user_viewing)

        return False

    def _build_liked_str(self, liked_user_names, self_liked=False, name_limit=2):
        """Builds a string from a list of user names"""
        if name_limit <= 0:
            raise ValueError("name_limit must be greater than 0")

        if not liked_user_names:
            return "0 likes"

        # Limit the number of names
        if len(liked_user_names) > name_limit:
            number_of_others = len(liked_user_names) - name_limit
            liked_user_names = liked_user_names[:name_limit]
            if number_of_others == 1:
                if self_liked:
                    liked_user_names.append("you")
                else:
                    liked_user_names.append("1 other")
            else:
                liked_user_names.append(f"{number_of_others} others")

        if len(liked_user_names) == 1:
            if self_liked:
                return "You liked this"
            else:
                return f"{liked_user_names[0]} liked this"
        else:
            english_list = ", ".join(liked_user_names[:-1])
            english_list = english_list + " and " + liked_user_names[-1]
            return f"Liked by {english_list}"

    def get_liked_str(self, for_user=None, for_user_friends=None):
        """Returns a string of the names of the users that liked the trip"""
        friends_liked = []
        others_liked = []
        self_liked = False

        for user in self.likes.all():
            if for_user and user == for_user:
                self_liked = True
                continue

            if for_user_friends and user in for_user_friends:
                friends_liked.append(user.name)
            else:
                others_liked.append(user.name)

        # Ensure the user's friends are shown first
        liked_user_names = []
        liked_user_names.extend(friends_liked)
        liked_user_names.extend(others_liked)
        if self_liked:
            liked_user_names.append("you")

        return self._build_liked_str(liked_user_names, self_liked)

    @property
    def has_distances(self):
        if self.horizontal_dist or self.vert_dist_down or self.vert_dist_up:
            return True
        elif self.aid_dist or self.surveyed_dist or self.resurveyed_dist:
            return True

    @property
    def distances(self):
        """Returns a list of distance fields that hold a value"""
        distances = {}
        for field in self._meta.fields:
            if isinstance(field, DistanceField):
                if getattr(self, field.name) > D(m=0):
                    distances[field.verbose_name.replace(" distance", "")] = getattr(
                        self, field.name
                    )
        return distances

    @property
    def is_private(self):
        if self.privacy == self.DEFAULT:
            return self.user.is_private
        elif self.privacy == self.PUBLIC:
            return False
        return True

    @property
    def is_public(self):
        if self.privacy == self.DEFAULT:
            return self.user.is_public
        elif self.privacy == self.PUBLIC:
            return True
        return False

    @property
    def has_report(self):
        return hasattr(self, "report") and self.report is not None

    @property
    def number(self):
        """Returns the 'index' of the trip by date"""
        qs = Trip.objects.filter(user=self.user).order_by("start", "-pk")
        index = list(qs.values_list("pk", flat=True)).index(self.pk)
        return index + 1


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
        return reverse("log:report_detail", kwargs={"pk": self.pk})

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
