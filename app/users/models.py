from __future__ import annotations

import os
import uuid
from datetime import timedelta
from functools import lru_cache

from django.contrib.auth import get_user_model
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.contrib.gis.measure import D
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator, RegexValidator
from django.db import models
from django.db.models import Count, Max, QuerySet, Sum
from django.http import HttpRequest
from django.urls import reverse
from django.utils import timezone as django_tz
from django.utils.functional import cached_property
from django_countries.fields import CountryField
from logger.models import Trip
from timezone_field import TimeZoneField

NoSpacesValidator = RegexValidator(
    r"^[^\s]*$",
    "This field cannot contain whitespace.",
)


def avatar_upload_path(instance, filename):
    """Returns the path to upload avatars to."""
    original_filename, ext = os.path.splitext(filename)
    avatar_uuid = uuid.uuid4().hex
    return f"avatars/{instance.uuid}/{avatar_uuid}{ext}"


class CavingUserManager(BaseUserManager):
    def create_user(self, email, username, name, password=None, **kwargs):
        """Creates a CavingUser."""
        if not email:
            raise ValueError("Users must have an email address")

        if not username:
            raise ValueError("Users must have a username")

        if not name:
            raise ValueError("Users must have a name")

        # Create user and save
        user = self.model(
            email=self.normalize_email(email),
            username=username.lower(),
            name=name,
            **kwargs,
        )

        if password:
            user.set_password(password)

        user.save(using=self._db)

        return user

    def create_superuser(self, email, username, name, password=None):
        """Creates a CavingUser which is a superuser."""
        user = self.create_user(
            email,
            username,
            name,
            password,
        )

        user.is_active = True
        user.is_superuser = True
        user.has_verified_email = True
        user.save(using=self._db)
        return user


class CavingUser(AbstractBaseUser, PermissionsMixin):
    """Custom user model containing social profile information and site settings."""

    #
    #  Authentication information
    #
    objects = CavingUserManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["username", "name"]

    uuid = models.UUIDField(
        verbose_name="UUID",
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text="A unique identifier for this user.",
    )
    email = models.EmailField(
        "email address",
        max_length=255,
        unique=True,
        help_text="This will be verified before you can log in.",
    )
    username = models.SlugField(
        max_length=30,
        unique=True,
        help_text=("A unique identifier that will be part of the web " "address for your logbook."),
    )
    name = models.CharField(
        max_length=35,
        help_text="Your name as you would like it to appear on your public profile.",
        default="Caver",
        validators=[MinLengthValidator(3)],
    )
    is_active = models.BooleanField(
        "Enabled user",
        default=False,
        help_text=(
            "Only enabled users are able to sign in. Users are "
            "disabled until their email is verified."
        ),
    )
    has_verified_email = models.BooleanField(
        "Email verified",
        default=False,
        help_text="Has the user verified their email address?",
    )
    has_mod_perms = models.BooleanField(
        "Moderator privileges",
        default=False,
        help_text="User has access to moderator level privileges.",
    )
    date_joined = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(default=django_tz.now)

    #
    #  Profile information
    #
    friends = models.ManyToManyField("self", blank=True)
    location = models.CharField(max_length=50, blank=True)
    country = CountryField(blank=True)
    bio = models.TextField(
        "biography",
        blank=True,
        help_text=(
            "Information about you that will be displayed on "
            "your public profile. "
            "Some <a href='https://www.markdownguide.org/basic-syntax/'>Markdown</a> "
            "is supported."
        ),
    )
    clubs = models.CharField(
        max_length=100,
        blank=True,
        help_text="A list of caving clubs or organisations that you are a member of.",
    )
    instagram = models.CharField(
        max_length=30,
        blank=True,
        validators=[NoSpacesValidator],
        help_text="Your Instagram username.",
    )
    facebook = models.CharField(
        max_length=50,
        validators=[MinLengthValidator(5), NoSpacesValidator],
        blank=True,
        help_text="Your Facebook username.",
    )
    x_username = models.CharField(
        max_length=15,
        blank=True,
        validators=[NoSpacesValidator],
        help_text="Your X username.",
        verbose_name="X/Twitter",
    )
    website = models.URLField(
        blank=True,
        help_text="A link to your personal website.",
    )

    # Avatar
    avatar = models.ImageField(
        upload_to=avatar_upload_path,
        verbose_name="profile picture",
        blank=True,
        help_text="A profile picture to display on your public profile.",
    )

    # Profile views
    profile_view_count = models.IntegerField(default=0)

    #
    #  Settings
    #

    # Distance units
    METRIC = "Metric"
    IMPERIAL = "Imperial"
    UNIT_CHOICES = [
        (METRIC, METRIC),
        (IMPERIAL, IMPERIAL),
    ]
    units = models.CharField(
        "Distance units",
        max_length=10,
        default=METRIC,
        choices=UNIT_CHOICES,
        help_text="Preferred units of distance.",
    )

    # User profile privacy
    PUBLIC = "Public"
    FRIENDS = "Friends"
    PRIVATE = "Private"
    PRIVACY_CHOICES = [
        (PUBLIC, "Anyone"),
        (FRIENDS, "Only my friends"),
        (PRIVATE, "Only me"),
    ]
    privacy = models.CharField(
        "Profile privacy",
        max_length=10,
        choices=PRIVACY_CHOICES,
        default=PRIVATE,
        help_text="Who can view your profile?",
    )

    # Privacy settings
    allow_friend_username = models.BooleanField(
        "Allow friend requests by username",
        default=True,
        help_text=(
            "If enabled, other users will be able to add you as a "
            "friend by entering your username. This will not affect your "
            "ability to add other users as friends."
        ),
    )
    allow_friend_email = models.BooleanField(
        "Allow friend requests by email",
        default=False,
        help_text=(
            "If enabled, other users will be able to add you as a "
            "friend by entering your email address. This will not affect your "
            "ability to add other users as friends."
        ),
    )
    allow_comments = models.BooleanField(
        "Allow comments on your trips",
        default=True,
        help_text=(
            "If enabled, other users will be able to comment on your trips. "
            "Disabling this setting will not delete any existing "
            "comments, but will hide them until it is re-enabled."
        ),
    )
    disable_distance_statistics = models.BooleanField(
        "Disable distance statistics",
        default=False,
        help_text=(
            "Enabling this option will mean that rope climbed, "
            "rope descended, horizontal distance and aid climbing "
            "distance statistics will not be displayed on your "
            "profile."
        ),
    )
    disable_survey_statistics = models.BooleanField(
        "Disable survey statistics",
        default=False,
        help_text=(
            "Enabling this option will mean that surveying and "
            "resurveying distance statistics will not be "
            "displayed on your profile."
        ),
    )
    disable_stats_over_time = models.BooleanField(
        "Disable statistics over time chart",
        default=False,
        help_text=(
            "Enabling this option will hide the statistics over "
            "time chart on the statistics page."
        ),
    )

    # Custom fields
    custom_field_1_label = models.CharField(
        "Custom field 1",
        max_length=25,
        blank=True,
    )
    custom_field_2_label = models.CharField(
        "Custom field 2",
        max_length=25,
        blank=True,
    )
    custom_field_3_label = models.CharField(
        "Custom field 3",
        max_length=25,
        blank=True,
    )
    custom_field_4_label = models.CharField(
        "Custom field 4",
        max_length=25,
        blank=True,
    )
    custom_field_5_label = models.CharField(
        "Custom field 5",
        max_length=25,
        blank=True,
    )

    # Feed settings
    # feed_ordering value should be a value which can be passed to
    # Trip.objects.order_by() to order trips in the feed.
    FEED_ADDED = "-added"
    FEED_DATE = "-start"
    FEED_ORDERING_CHOICES = [
        (FEED_ADDED, "Recently added"),
        (FEED_DATE, "Trip date"),
    ]
    feed_ordering = models.CharField(
        default=FEED_ADDED,
        max_length=15,
        choices=FEED_ORDERING_CHOICES,
    )

    # All other settings
    timezone = TimeZoneField(
        default="Europe/London",
        choices_display="WITH_GMT_OFFSET",
        help_text="Timezone to enter and display dates and times in.",
    )

    # Email settings
    email_friend_requests = models.BooleanField(
        "Email me new friend requests",
        default=True,
        help_text="Send an email when another user adds you as a friend.",
    )
    email_comments = models.BooleanField(
        "Email me new comments",
        default=True,
        help_text=("Send an email when another user comments on a trip you are following."),
    )

    class Meta:
        verbose_name = "user"

    def __str__(self):
        return self.name

    def get_full_name(self):
        return self.name

    def get_short_name(self):
        return self.name

    def get_absolute_url(self):
        return reverse("log:user", args=[self.username])

    def save(self, *args, **kwargs):
        # Lowercase the username
        self.username = self.username.lower()

        # Ensure a user cannot add themselves as a friend
        # self._state.adding is True when the object is being created
        if self._state.adding is False and self in self.friends.all():
            self.friends.remove(self)
        return super().save(*args, **kwargs)

    def notify(self, message, url):
        """Send a notification to this user."""
        return Notification.objects.create(user=self, message=message, url=url)

    def is_viewable_by(self, user_viewing, /, friends=None):
        """Returns whether or not user_viewing can view this profile."""
        if self == user_viewing:
            return True

        if self.privacy == User.PUBLIC:
            return True

        if self.privacy == User.FRIENDS:
            if friends is None:
                friends = self.friends.all()

            if user_viewing in friends:
                return True

        return False

    def mutual_friends(self, other_user):
        if not other_user.is_authenticated:
            return self.friends.none()

        other_user_friends_pks = other_user.friends.values_list("pk", flat=True)
        return self.friends.filter(pk__in=other_user_friends_pks).annotate(
            num_trips=Count("trip", distinct=True),
        )

    def get_photos(self, for_user: CavingUser | None = None):
        """Returns a QuerySet of photos uploaded by this user.

        If `for_user` is specified, only photos which are viewable by that user
        will be returned.
        """
        from logger.models import TripPhoto

        if for_user is None:
            return TripPhoto.objects.valid().filter(user=self)

        qs = (
            TripPhoto.objects.valid()
            .filter(user=self)
            .select_related("trip", "trip__user", "user")
            .order_by("-trip__added", "-taken")
        )

        # Remove photos from trips which are not viewable by the user
        friends = self.friends.all()
        for photo in qs:
            if not photo.trip.is_viewable_by(for_user, friends):
                qs = qs.exclude(pk=photo.pk)
            if photo.trip.private_photos and photo.trip.user != for_user:
                qs = qs.exclude(pk=photo.pk)

        return qs

    def add_profile_view(self, request: HttpRequest):
        if request.user == self or request.user.is_anonymous:
            return

        self.profile_view_count += 1
        self.save(update_fields=["profile_view_count"])

    @property
    def trips(self):
        return Trip.objects.filter(user=self)

    @property
    def trips_for_stats(self):
        return self.trips.exclude(type=Trip.SURFACE)

    @property
    def has_trips(self):
        return self.trips.count() > 0

    @property
    def is_private(self):
        return self.privacy != self.PUBLIC

    @property
    def is_public(self):
        return self.privacy == self.PUBLIC

    @property
    def is_staff(self):
        return self.is_superuser

    @property
    def is_moderator(self):
        return bool(self.is_superuser or self.has_mod_perms)

    @property
    def total_trip_duration(self):
        return self.trips.exclude(type=Trip.SURFACE).aggregate(Sum("duration"))["duration__sum"]

    @lru_cache
    def _sum_distance_field(self, qs: QuerySet, field_name: str) -> D:
        """Return the total distance for the given field."""
        if qs is None:
            qs = self.trips_for_stats

        total = D(m=0)
        for trip in qs:
            total += getattr(trip, field_name)
        return total

    @lru_cache
    def total_vert_dist_up(self, qs: QuerySet | None = None):
        return self._sum_distance_field(qs, "vert_dist_up")

    @lru_cache
    def total_vert_dist_down(self, qs: QuerySet | None = None):
        return self._sum_distance_field(qs, "vert_dist_down")

    @lru_cache
    def total_surveyed(self, qs: QuerySet | None = None):
        return self._sum_distance_field(qs, "surveyed_dist")

    @lru_cache
    def total_resurveyed(self, qs: QuerySet | None = None):
        return self._sum_distance_field(qs, "resurveyed_dist")

    @lru_cache
    def total_aid_climbed(self, qs: QuerySet | None = None):
        return self._sum_distance_field(qs, "aid_dist")

    @lru_cache
    def total_horizontal(self, qs: QuerySet | None = None):
        return self._sum_distance_field(qs, "horizontal_dist")

    @cached_property
    def quick_stats(self):
        qs = self.trips.exclude(type=Trip.SURFACE).aggregate(
            qs_trips=Count("pk", distinct=True),
            qs_cavers=Count("cavers", distinct=True),
            qs_longest_trip=Max("duration", default=timedelta()),
        )
        qs["qs_duration"] = self.total_trip_duration
        qs["qs_friends"] = self.friends.count()
        qs["qs_photos"] = self.get_photos().count()
        qs["qs_joined"] = self.date_joined
        qs["qs_last_trip"] = self.trips.order_by("-start").first()

        stats_qs = self.trips_for_stats
        qs["qs_climbed"] = self.total_vert_dist_up(stats_qs)
        qs["qs_descended"] = self.total_vert_dist_down(stats_qs)
        qs["qs_surveyed"] = self.total_surveyed(stats_qs)
        qs["qs_resurveyed"] = self.total_resurveyed(stats_qs)
        qs["qs_aid_climbed"] = self.total_aid_climbed(stats_qs)
        qs["qs_horizontal"] = self.total_horizontal(stats_qs)
        return qs

    @property
    def has_social_media_links(self):
        return self.instagram or self.facebook or self.x_username or self.website

    @property
    def get_instagram_url(self):
        return f"https://www.instagram.com/{self.instagram}/"  # noqa: E231

    @property
    def get_facebook_url(self):
        return f"https://www.facebook.com/{self.facebook}/"  # noqa: E231

    @property
    def get_x_url(self):
        return f"https://x.com/{self.x_username}/"  # noqa: E231

    @property
    def get_website_url(self):
        return self.website


User = get_user_model()


class Notification(models.Model):
    FREE_TEXT = "A"
    TRIP_LIKE = "B"
    TRIP_COMMENT = "C"
    TYPE_CHOICES = [
        (FREE_TEXT, "Free text"),
        (TRIP_LIKE, "Trip like"),
        (TRIP_COMMENT, "Trip comment"),
    ]

    type = models.CharField(max_length=2, default="A", choices=TYPE_CHOICES)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    read = models.BooleanField(
        default=False, help_text="Has the notification been read by the user?"
    )
    added = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField()

    # Freeform specific fields
    message = models.CharField(max_length=255, blank=True)
    url = models.URLField("URL", max_length=255, blank=True)

    # Trip specific fields
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.get_message()

    def save(self, updated=True, *args, **kwargs):
        if updated:
            self.updated = django_tz.now()
        return super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("users:notification", args=[self.pk])

    def clean(self):
        """Ensure that different types of notifications have the correct fields."""
        if self.type == self.FREE_TEXT:
            if not self.message or not self.url:
                raise ValidationError("Free text notifications must have both a message and a URL.")
        elif self.type == self.TRIP_LIKE or self.type == self.TRIP_COMMENT:
            if not self.trip:
                raise ValidationError(
                    "Trip like or trip comment notifications "
                    "must have a trip associated with them."
                )

            if self.message or self.url:
                raise ValidationError(
                    "Trip like or trip comment notifications " "must not have a message or URL."
                )

            if self.type == self.TRIP_COMMENT:
                raise NotImplementedError
        else:
            raise ValidationError("Invalid notification type")

    def get_url(self) -> str:
        assert self.trip is not None

        if self.type == self.FREE_TEXT:
            return self.url
        if self.type == self.TRIP_LIKE or self.type == self.TRIP_COMMENT:
            return self.trip.get_absolute_url()
        raise RuntimeError("Invalid notification type")

    def get_message(self) -> str:
        if self.type == self.FREE_TEXT:
            return self.message
        if self.type == self.TRIP_LIKE:
            return self._get_trip_like_message()
        if self.type == self.TRIP_COMMENT:
            return self._get_trip_comment_message()
        raise RuntimeError("Invalid notification type")

    def _get_trip_like_message(self) -> str:
        assert self.trip is not None

        assert self.type == self.TRIP_LIKE
        users = list(self.trip.likes.exclude(pk=self.user.pk))
        return self._get_trip_action_message(
            users=users,
            action="like",
            action_str="liked by",
        )

    def _get_trip_comment_message(self) -> str:
        assert self.type == self.TRIP_COMMENT and self.trip is not None

        users = []
        for comment in self.trip.comments.all():
            if comment.author == self.user:
                continue
            if comment.author in users:
                continue

            users.append(comment.author)

        return self._get_trip_action_message(
            users=users,
            action="comment",
            action_str="commented on by",
        )

    def _get_trip_action_message(
        self, /, users: list[CavingUser], action: str, action_str: str
    ) -> str:
        assert self.trip is not None

        user_count = len(users)

        prefix = f"{self.trip.user.name}'s trip to"
        if self.user == self.trip.user:
            prefix = "Your trip to"

        if user_count < 1:
            return f"{prefix} {self.trip.cave_name} received {action}s."

        if user_count == 1:
            user = users[0].name
            return f"{prefix} {self.trip.cave_name} was {action_str} {user}."

        if user_count == 2:
            user1 = users[0].name
            user2 = users[1].name
            return f"{prefix} {self.trip.cave_name} was {action_str} " f"{user1} and {user2}."

        if user_count > 2:
            user1 = users[0].name
            user2 = users[1].name

            num_others = user_count - 2
            result = (
                f"{prefix} {self.trip.cave_name} was {action_str} "
                f"{user1}, {user2} and {num_others} "
            )

            if num_others == 1:
                return result + "other person."
            return result + "others."

        raise RuntimeError("Impossible state reached in TripLikeNotification.get_message()")


class FriendRequest(models.Model):
    user_from = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="friend_requests_sent"
    )
    user_to = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="friend_requests_received"
    )
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user_from", "user_to"], name="unique_friend_request")
        ]

    def __str__(self):
        return f"{self.user_from} -> {self.user_to}"
