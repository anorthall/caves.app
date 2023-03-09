from django.test import TestCase
from django.utils import timezone
from django.utils.timezone import datetime as dt
from django.contrib.auth import get_user_model
from .models import Trip


class TripTestCase(TestCase):
    def setUp(self):
        # Test user to enable trip creation
        user = get_user_model().objects.create_user(
            email="test@test.com",
            username="testusername",
            password="password",
            first_name="Firstname",
            last_name="Lastname",
        )

        # Trip with a start and end time
        Trip.objects.create(
            user=user,
            cave_name="Test Cave 1",
            cave_region="Test Region",
            cave_country="Test Country",
            trip_start=dt.fromisoformat("2010-01-01T12:00:00+00:00"),
            trip_end=dt.fromisoformat("2010-01-01T14:00:00+00:00"),
        )

        # Trip with no end time
        Trip.objects.create(
            user=user,
            cave_name="Test Cave 2",
            cave_region="Test Region",
            cave_country="Test Country",
            trip_start=dt.fromisoformat("2010-01-01T12:00:00+00:00"),
        )

    def test_trip_duration(self):
        """
        Check that trip duration returns a timedelta with the correct value
        Check that trip duration returns None if no trip_end time
        """
        trip_with_end = Trip.objects.get(pk=1)
        trip_without_end = Trip.objects.get(pk=2)

        self.assertNotEqual(trip_with_end.trip_end, None)
        self.assertEqual(trip_with_end.duration(), timezone.timedelta(hours=2))

        self.assertEqual(trip_without_end.trip_end, None)
        self.assertEqual(trip_without_end.duration(), None)
