import os
import uuid

from django.contrib.auth import get_user_model
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.core.validators import MinLengthValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone as django_tz
from django_countries.fields import CountryField
from logger.models import Trip, TripReport
from timezone_field import TimeZoneField


def avatar_upload_path(instance, filename):
    """Returns the path to upload avatars to"""
    original_filename, ext = os.path.splitext(filename)
    return f"avatars/{instance.uuid}/avatar{ext}"


class CavingUserManager(BaseUserManager):
    def create_user(self, email, username, name, password=None, **kwargs):
        """Creates a CavingUser"""
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
        """Creates a CavingUser which is a superuser"""
        user = self.create_user(
            email,
            username,
            name,
            password,
        )

        user.is_active = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class CavingUser(AbstractBaseUser, PermissionsMixin):
    """Custom user model containing social profile information and site settings"""

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
        help_text=(
            "A unique identifier that will be part of the web "
            "address for your logbook."
        ),
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
    page_title = models.CharField(
        max_length=50,
        blank=True,
        help_text=(
            "A title to display on your profile page (if enabled). "
            "If left blank it will use your full name."
        ),
    )

    # Avatar
    avatar = models.ImageField(
        upload_to=avatar_upload_path,
        verbose_name="profile picture",
        blank=True,
        help_text="A profile picture to display on your public profile.",
    )

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
            "If enabled, other users will be able to comment on your trips "
            "and trip reports. Disabling this setting will not delete any existing "
            "comments, but will hide them until it is re-enabled."
        ),
    )
    public_statistics = models.BooleanField(
        "Show statistics on profile",
        default=True,
        help_text=(
            "Enabling this option will show an annual statistics table on your "
            "profile page which will be visible to anyone who can view your profile."
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
    show_cavers_on_trip_list = models.BooleanField(
        "Show cavers on trip list",
        default=True,
        help_text=(
            "Enabling this option will display a list of cavers "
            "beneath each trip on your profile trip list."
        ),
    )
    private_notes = models.BooleanField(
        "Keep notes private",
        default=True,
        help_text=(
            "Enable this option to prevent your trip notes being "
            "displayed to other users when they view your trips."
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
        "Friend request emails",
        default=True,
        help_text="Send an email when another user adds you as a friend.",
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
        """Send a notification to this user"""
        return Notification.objects.create(user=self, message=message, url=url)

    def is_viewable_by(self, user_viewing, /, friends=None):
        """Returns whether or not user_viewing can view this profile"""
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
        return self.friends.filter(pk__in=other_user_friends_pks)

    @property
    def trips(self):
        return Trip.objects.filter(user=self)

    @property
    def reports(self):
        return TripReport.objects.filter(user=self)

    @property
    def has_trips(self):
        return self.trips.count() > 0

    @property
    def is_private(self):
        if self.privacy == self.PUBLIC:
            return False
        return True

    @property
    def is_public(self):
        if self.privacy == self.PUBLIC:
            return True
        return False

    @property
    def is_staff(self):
        return self.is_superuser


User = get_user_model()


class Notification(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    message = models.CharField(max_length=255)
    url = models.URLField("URL", max_length=255)
    read = models.BooleanField(
        default=False, help_text="Has the notification been read by the user?"
    )
    added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message


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
            models.UniqueConstraint(
                fields=["user_from", "user_to"], name="unique_friend_request"
            )
        ]

    def __str__(self):
        return f"{self.user_from} -> {self.user_to}"
