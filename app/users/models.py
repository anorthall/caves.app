from django.contrib.auth import get_user_model
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.core.validators import MinLengthValidator
from django.db import models
from django.utils import timezone as django_tz
from django_countries.fields import CountryField
from logger.models import Trip, TripReport
from timezone_field import TimeZoneField


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
            "Information about you that will be displayed on " "your public profile."
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
        "Show statistics",
        default=True,
        help_text=(
            "Check this box to show a statistics table on your "
            "public profile (if enabled)."
        ),
    )
    private_notes = models.BooleanField(
        "Keep notes private",
        default=True,
        help_text=(
            "Check this box to prevent your trip notes being "
            "displayed on your public profile (if enabled)."
        ),
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

    class Meta:
        verbose_name = "user"

    def __str__(self):
        return self.name

    def get_full_name(self):
        return self.name

    def get_short_name(self):
        return self.name

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
        from users.models import Notification

        return Notification.objects.create(user=self, message=message, url=url)

    def is_viewable_by(self, user_viewing):
        """Returns whether or not user_viewing can view this profile"""
        if self == user_viewing:
            return True

        if self.privacy == User.PUBLIC:
            return True

        if self.privacy == User.FRIENDS:
            if user_viewing in self.friends.all():
                return True

        return False

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
    user = models.ForeignKey(User, on_delete=models.CASCADE)
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
