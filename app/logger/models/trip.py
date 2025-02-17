from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import humanize
from distancefield import D, DistanceField, DistanceUnitField
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.http.request import HttpRequest
from django.urls import reverse

from ..validators import (
    above_zero_dist_validator,
    horizontal_dist_validator,
    vertical_dist_validator,
)

if TYPE_CHECKING:
    from users.models import CavingUser


class Caver(models.Model):
    """A caver that was on a trip."""

    name = models.CharField(max_length=40)
    added = models.DateTimeField("caver added on", auto_now_add=True)
    updated = models.DateTimeField("caver last updated", auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    linked_account = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="linked_cavers",
    )
    uuid = models.UUIDField(
        verbose_name="UUID",
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text="A unique identifier for this caver.",
    )

    def __str__(self):
        return self.name

    def total_trip_duration(self):
        return self.trip_set.aggregate(Sum("duration"))["duration__sum"]

    def total_trip_duration_str(self):
        td = self.total_trip_duration()
        if td:
            return humanize.precisedelta(td, minimum_unit="minutes", suppress=["months", "years"])
        return None

    def save(self, *args, **kwargs):
        self.name = self.name.strip()

        if self.linked_account not in self.user.friends.all():
            self.linked_account = None

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("log:caver_detail", args=[self.uuid])


# noinspection PyUnresolvedReferences
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
    cave_name = models.CharField(
        max_length=100,
        help_text="The name of the cave or cave system entered.",
    )
    cave_entrance = models.CharField(
        "entrance",
        max_length=100,
        blank=True,
        help_text="The location at which you entered the cave.",
    )
    cave_exit = models.CharField(
        "exit",
        max_length=100,
        blank=True,
        help_text="The location at which you exited the cave.",
    )
    cave_location = models.CharField(
        "location",
        max_length=100,
        blank=True,
        help_text=(
            "Enter a decimal latitude and longitude, "
            "address, or place name. "
            "Cave locations are not visible to other users."
        ),
    )
    cave_coordinates = models.PointField(
        "coordinates",
        blank=True,
        null=True,
        default=None,
        geography=True,
        help_text="The coordinates of the cave in WGS84 format.",
    )
    cave_region = models.CharField(
        "region",
        max_length=100,
        blank=True,
        help_text="The state or region in which the cave is located.",
    )
    cave_country = models.CharField(
        "country",
        max_length=100,
        blank=True,
        help_text="The country in which the cave is located.",
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
    cavers_old = models.CharField(
        max_length=250,
        blank=True,
        help_text=(
            "A comma-separated list of cavers that were on this trip. "
            "Avoid adding yourself to this list."
        ),
    )
    cavers = models.ManyToManyField(
        Caver,
        blank=True,
        help_text="A list of cavers that were on this trip.",
    )
    clubs = models.CharField(
        max_length=100,
        blank=True,
        help_text="A comma-separated list of any caving clubs associated with this trip.",
    )
    expedition = models.CharField(
        max_length=100,
        blank=True,
        help_text="A comma-separated list of any expeditions associated with this trip.",
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

    # Custom fields
    custom_field_1 = models.CharField(
        max_length=200,
        blank=True,
    )
    custom_field_2 = models.CharField(
        max_length=200,
        blank=True,
    )
    custom_field_3 = models.CharField(
        max_length=200,
        blank=True,
    )
    custom_field_4 = models.CharField(
        max_length=200,
        blank=True,
    )
    custom_field_5 = models.CharField(
        max_length=100,
        blank=True,
    )

    # Notes
    notes = models.TextField(
        blank=True,
        verbose_name="private notes",
        help_text=(
            "Notes that will only ever be visible to you. "
            "Some <a href='https://www.markdownguide.org/basic-syntax/'>Markdown</a> "
            "is supported."
        ),
    )

    public_notes = models.TextField(
        blank=True,
        help_text=(
            "These notes will be visible to anyone who can view the trip. "
            "Some <a href='https://www.markdownguide.org/basic-syntax/'>Markdown</a> "
            "is supported."
        ),
    )

    # Metadata
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="liked_trips")
    followers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="followed_trips"
    )
    view_count = models.IntegerField(default=0)
    featured_photo = models.ForeignKey(
        "logger.TripPhoto",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="trips_featured",
    )
    privacy = models.CharField(
        "Who can view this trip?",
        max_length=10,
        choices=PRIVACY_CHOICES,
        default=DEFAULT,
    )
    private_photos = models.BooleanField(
        "Hide photos from public view?",
        default=False,
        help_text=(
            "If this is ticked, photos uploaded to this trip will only be visible to "
            "you, regardless of who can view the trip."
        ),
    )
    added = models.DateTimeField("trip added on", auto_now_add=True)
    updated = models.DateTimeField("trip last updated", auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uuid = models.UUIDField(
        verbose_name="UUID",
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text="A unique identifier for this trip.",
    )

    def __str__(self):
        return self.cave_name

    def _set_duration(self):
        """Store the duration in the database as a timedelta."""
        if self.end:
            self.duration = self.end - self.start
        else:
            self.duration = None
        return self.duration

    def _set_duration_str(self):
        """Store the duration in the database as a string."""
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
            if isinstance(field, DistanceField) and getattr(self, field.name) == 0:
                setattr(self, field.name, None)

        # If `trip.cave_location` is not set, unset `trip.cave_coordinates`
        if not self.cave_location:
            self.cave_coordinates = None

        return super().save(*args, **kwargs)

    def clean(self):
        # Check self.start exists - may have been removed by form validation
        # If it does not exist 'for real', the form/low level model validation
        # will catch it.
        if self.start and self.end and self.start > self.end:
            raise ValidationError("The trip start time must be before the trip end time.")

    def get_absolute_url(self):
        return reverse("log:trip_detail", args=[self.uuid])

    def is_viewable_by(self, user_viewing: CavingUser | AnonymousUser | None, /, friends=None):
        """Returns whether or not user_viewing can view this trip."""
        if isinstance(user_viewing, AnonymousUser | None) and self.privacy == self.DEFAULT:
            return self.user.is_public

        if isinstance(user_viewing, AnonymousUser | None) or self.privacy == self.PUBLIC:
            return self.privacy == self.PUBLIC

        if friends is None:
            friends = self.user.friends.all()

        if user_viewing == self.user:
            return True

        if self.privacy == self.FRIENDS and user_viewing in friends:
            return True

        if self.privacy == self.DEFAULT:
            return self.user.is_viewable_by(user_viewing, friends)

        return False

    def _build_liked_str(self, liked_user_names, self_liked=False, name_limit=2):
        """Builds a string from a list of user names."""
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
            return f"{liked_user_names[0]} liked this"
        english_list = ", ".join(liked_user_names[:-1])
        english_list = english_list + " and " + liked_user_names[-1]
        return f"Liked by {english_list}"

    def get_liked_str(self, for_user=None, for_user_friends=None):
        """Returns a string of the names of the users that liked the trip."""
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

    def add_view(self, request: HttpRequest, commit=True):
        if request.user.is_anonymous or self.user == request.user:
            return

        self.view_count += 1
        if commit:
            self.save(update_fields=["view_count"])

    @property
    def latitude(self):
        return self.cave_coordinates.y if self.cave_coordinates else None

    @property
    def longitude(self):
        return self.cave_coordinates.x if self.cave_coordinates else None

    @property
    def has_distances(self):
        if (
            self.horizontal_dist
            or self.vert_dist_down
            or self.vert_dist_up
            or self.aid_dist
            or self.surveyed_dist
            or self.resurveyed_dist
        ):
            return True
        return None

    @property
    def distances(self):
        """Returns a list of distance fields that hold a value."""
        distances = {}
        for field in self._meta.fields:
            if isinstance(field, DistanceField) and getattr(self, field.name) > D(m=0):
                distances[field.verbose_name.replace(" distance", "")] = getattr(self, field.name)
        return distances

    @property
    def is_private(self):
        if self.privacy == self.DEFAULT:
            return self.user.is_private
        return self.privacy != self.PUBLIC

    @property
    def is_public(self):
        if self.privacy == self.DEFAULT:
            return self.user.is_public
        return self.privacy == self.PUBLIC

    @property
    def number(self):
        """Returns the 'index' of the trip by date."""
        qs = Trip.objects.filter(user=self.user).order_by("start", "-pk")
        index = list(qs.values_list("pk", flat=True)).index(self.pk)
        return index + 1

    @property
    def custom_fields(self) -> tuple[tuple[str, str], ...]:
        """Returns a tuple of (field_label, value) for valid custom fields."""
        valid_fields: list[tuple[str, str]] = []
        for field in self._meta.fields:
            if not field.name.startswith("custom_field_"):
                continue

            label_field_name = f"{field.name}_label"
            if not hasattr(self.user, label_field_name):  # pragma: no cover
                continue

            label = getattr(self.user, label_field_name)
            if not label:
                continue

            value = getattr(self, field.name)
            if value:
                valid_fields.append((label, value))

        return tuple(valid_fields)

    @property
    def valid_photos(self):
        return self.photos.filter(
            is_valid=True,
            deleted_at=None,
            photo_type="DE",
        ).order_by("taken", "added")

    @property
    def feed_photos(self):
        return self.valid_photos.order_by("?")[:10]
