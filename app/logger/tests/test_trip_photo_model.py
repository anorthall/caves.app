from unittest.mock import MagicMock

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, tag
from django.utils import timezone

from ..models import Trip, trip_photo_upload_path

User = get_user_model()


@tag("logger", "tripphoto", "fast", "unit")
class TripPhotoModelUnitTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.user = User.objects.create_user(
            email="test@users.app",
            name="Test User",
            username="testuser",
            password="password",
        )
        self.user.is_active = True
        self.user.save()

        self.trip = Trip.objects.create(
            user=self.user,
            cave_name="Test Cave",
            start=timezone.now(),
        )

    def test_trip_photo_upload_path(self):
        """Test that the upload path is correct."""
        instance = MagicMock()
        instance.user = self.user
        instance.trip = self.trip
        instance.uuid = "12345678-1234-5678-1234-567812345678"
        filename = "test-file.jpg"

        expected = (
            f"photos/{instance.user.uuid}/{instance.trip.uuid}/{instance.uuid}.jpg"
        )
        actual = trip_photo_upload_path(instance, filename)
        self.assertEqual(expected, actual)
