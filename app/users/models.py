from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django_countries.fields import CountryField
from django.db import models
from timezone_field import TimeZoneField
from logger.models import Trip


class CavingUserManager(BaseUserManager):
    def create_user(self, email, username, first_name, last_name, password=None):
        """Creates a CavingUser"""

        if not email:
            raise ValueError("Users must have an email address")

        if not username:
            raise ValueError("Users must have a username")

        if not first_name or not last_name:
            raise ValueError("Users must have a first and last name")

        user = self.model(
            email=self.normalize_email(email),
            username=username.lower(),
            first_name=first_name,
            last_name=last_name,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, first_name, last_name, password=None):
        """Creates a CavingUser which is a superuser"""
        user = self.create_user(
            email,
            username,
            first_name,
            last_name,
            password,
        )

        user.is_active = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class CavingUser(AbstractBaseUser, PermissionsMixin):
    # Email is used as login username
    email = models.EmailField(
        "email address",
        max_length=255,
        unique=True,
        help_text="This will be verified before you can log in.",
    )

    # Username for URLs
    username = models.SlugField(
        max_length=30,
        unique=True,
        help_text="A unique identifier that will be part of the web address for your logbook.",
    )

    # Personal information
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    location = models.CharField(max_length=50, blank=True)
    country = CountryField(blank=True)
    bio = models.TextField(
        "about me",
        blank=True,
        help_text="Information about you that will be displayed on your public profile.",
    )
    club = models.CharField(
        max_length=50,
        blank=True,
        help_text="A list of caving clubs or organisations that you are a member of.",
    )

    # Unit settings
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
        help_text="Units of distance to display/enter data in.",
    )

    # Privacy settings
    PUBLIC = "Public"
    PRIVATE = "Private"
    PRIVACY_TYPES = [
        (PUBLIC, PUBLIC),
        (PRIVATE, PRIVATE),
    ]
    privacy = models.CharField(
        "Profile privacy",
        max_length=10,
        choices=PRIVACY_TYPES,
        default=PRIVATE,
        help_text="Whether your profile is public or private.",
    )

    # Timezone settings
    timezone = TimeZoneField(
        default="Europe/London",
        choices_display="WITH_GMT_OFFSET",
        help_text="Timezone to enter/display dates and times in.",
    )

    # is_active determines if a user can log in or not
    is_active = models.BooleanField(
        "Enabled user",
        default=False,
        help_text="Only enabled users are able to sign in. Users are disabled until their email is verified.",
    )
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    objects = CavingUserManager()

    class Meta:
        verbose_name = "user"

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_short_name(self):
        return self.first_name

    def clean(self):
        self.username = self.username.lower()

    def trips(self):
        return Trip.objects.filter(user=self)

    def has_trips(self):
        return self.trips().count() > 1

    def is_private(self):
        if self.privacy == self.PUBLIC:
            return False
        return True

    def is_public(self):
        if self.privacy == self.PUBLIC:
            return True
        return False

    @property
    def is_staff(self):
        return self.is_superuser
