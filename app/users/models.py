from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from timezone_field import TimeZoneField


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

        user.email_verified = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class CavingUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField("email address", max_length=255, unique=True)
    username = models.SlugField(
        max_length=30,
        unique=True,
        help_text="A unique identifier that will be part of the web address for your logbook.",
    )
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    location = models.CharField(max_length=50, blank=True)
    bio = models.TextField("about me", blank=True)

    timezone = TimeZoneField(default="Europe/London", choices_display="WITH_GMT_OFFSET")

    METRIC = "Metric"
    IMPERIAL = "Imperial"
    UNIT_CHOICES = [
        (METRIC, METRIC),
        (IMPERIAL, IMPERIAL),
    ]
    units = models.CharField(
        "Distance units", max_length=10, default=METRIC, choices=UNIT_CHOICES
    )

    is_active = models.BooleanField("enabled user?", default=True)

    email_verified = models.BooleanField("email verified?", default=False)

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

    @property
    def is_staff(self):
        return self.is_superuser
