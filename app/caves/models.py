import uuid as uuid

from django.contrib.gis.db import models
from django_countries.fields import CountryField


class CaveSystemManager(models.Manager):
    def by(self, user):
        return self.filter(user=user)


class CaveSystem(models.Model):
    name = models.CharField(max_length=100)
    uuid = models.UUIDField("UUID", default=uuid.uuid4, editable=False, unique=True)
    added = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    user = models.ForeignKey("users.CavingUser", on_delete=models.CASCADE)
    objects = CaveSystemManager()

    def __str__(self):
        return self.name


class CaveEntrance(models.Model):
    name = models.CharField(max_length=255)
    system = models.ForeignKey(
        CaveSystem, on_delete=models.CASCADE, related_name="entrances"
    )
    region = models.CharField(
        max_length=100,
        blank=True,
        help_text="The state or region in which the cave is located.",
    )
    country = CountryField()
    location = models.CharField(
        max_length=100,
        blank=True,
        help_text=(
            "Enter a decimal latitude and longitude, "
            "address, or place name. "
            "Cave locations are not visible to other users."
        ),
    )
    coordinates = models.PointField(
        blank=True,
        null=True,
        geography=True,
        help_text="The coordinates of the cave in WGS84 format.",
    )

    uuid = models.UUIDField("UUID", default=uuid.uuid4, editable=False, unique=True)
    added = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.system.name})"

    @property
    def user(self):
        return self.system.user
