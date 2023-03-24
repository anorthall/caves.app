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
        user.is_active = True
        user.save()

        # Trip with a start and end time
        Trip.objects.create(
            user=user,
            cave_name="Test Cave 1",
            start=dt.fromisoformat("2010-01-01T12:00:00+00:00"),
            end=dt.fromisoformat("2010-01-01T14:00:00+00:00"),
        )

        # Trip with no end time
        Trip.objects.create(
            user=user,
            cave_name="Test Cave 2",
            start=dt.fromisoformat("2010-01-01T12:00:00+00:00"),
        )

    def test_trip_duration(self):
        """
        Check that trip duration returns a timedelta with the correct value
        Check that trip duration returns None if no end time
        """
        trip_with_end = Trip.objects.get(cave_name="Test Cave 1")
        trip_without_end = Trip.objects.get(cave_name="Test Cave 2")

        self.assertNotEqual(trip_with_end.end, None)
        self.assertEqual(trip_with_end.duration, timezone.timedelta(hours=2))

        self.assertEqual(trip_without_end.end, None)
        self.assertEqual(trip_without_end.duration, None)

    def test_trip_duration_str(self):
        """Check that the trip duration string returns the correct value"""
        trip = Trip.objects.get(cave_name="Test Cave 1")
        self.assertEqual(trip.duration_str, "2 hours")

        trip = Trip.objects.get(cave_name="Test Cave 1")  # Cached, grab again
        trip.end = dt.fromisoformat("2010-01-02T13:01:00+00:00")
        self.assertEqual(trip.duration_str, "1 day, 1 hour and 1 minute")

        trip = Trip.objects.get(cave_name="Test Cave 1")  # Cached, grab again
        trip.end = dt.fromisoformat("2010-01-03T14:02:00+00:00")
        self.assertEqual(trip.duration_str, "2 days, 2 hours and 2 minutes")

    def test_trip_privacy(self):
        """Test the Trip.is_private and Trip.is_public methods"""
        trip = Trip.objects.get(cave_name="Test Cave 1")
        user = trip.user

        # Check that privacy is correctly inherited from the user
        self.assertEqual(user.privacy, get_user_model().PRIVATE)
        self.assertEqual(trip.privacy, Trip.DEFAULT)
        self.assertTrue(trip.is_private())
        self.assertFalse(trip.is_public())

        # Same again, but for a profile setting of public
        user.privacy = get_user_model().PUBLIC
        user.save()
        trip = Trip.objects.get(cave_name="Test Cave 1")
        self.assertEqual(user.privacy, get_user_model().PUBLIC)
        self.assertTrue(trip.is_public())
        self.assertFalse(trip.is_private())

        # Now test trip specific privacy
        trip.privacy = Trip.PRIVATE
        self.assertEqual(trip.privacy, Trip.PRIVATE)
        self.assertTrue(trip.is_private())
        self.assertFalse(trip.is_public())

        trip.privacy = Trip.PUBLIC
        self.assertEqual(trip.privacy, Trip.PUBLIC)
        self.assertTrue(trip.is_public())
        self.assertFalse(trip.is_private())
