from django.test import TestCase
from django.utils import timezone
from django.utils.timezone import datetime as dt
from django.contrib.gis.measure import D
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
        user.privacy = get_user_model().PRIVATE
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

        # Create several trips with different privacy settings
        Trip.objects.create(  # Private
            user=user,
            cave_name="Test Cave 3",
            start=dt.fromisoformat("2010-01-01T12:00:00+00:00"),
            privacy=Trip.PRIVATE,
        )
        Trip.objects.create(  # Public
            user=user,
            cave_name="Test Cave 4",
            start=dt.fromisoformat("2010-01-01T12:00:00+00:00"),
            privacy=Trip.PUBLIC,
        )
        Trip.objects.create(  # Default
            user=user,
            cave_name="Test Cave 5",
            start=dt.fromisoformat("2010-01-01T12:00:00+00:00"),
            privacy=Trip.DEFAULT,
        )

        # Create a trip to test tidbits
        Trip.objects.create(
            user=user,
            cave_name="Test Cave 6",
            start=dt.fromisoformat("2010-01-01T12:00:00+00:00"),
            end=dt.fromisoformat("2010-01-01T14:00:00+00:00"),
            vert_dist_down="100m",
            vert_dist_up="200m",
            horizontal_dist="300m",
            surveyed_dist="400m",
            aid_dist="500m",
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

    def test_trip_is_private_and_is_public(self):
        """Test the Trip.is_private and Trip.is_public methods"""
        trip_private = Trip.objects.get(cave_name="Test Cave 3")
        trip_public = Trip.objects.get(cave_name="Test Cave 4")
        trip_default = Trip.objects.get(cave_name="Test Cave 5")

        self.assertTrue(trip_private.is_private)
        self.assertFalse(trip_private.is_public)

        self.assertFalse(trip_public.is_private)
        self.assertTrue(trip_public.is_public)

        self.assertTrue(trip_default.is_private)
        self.assertFalse(trip_default.is_public)

    def test_trip_str(self):
        """Test the Trip.__str__ method"""
        trip = Trip.objects.get(cave_name="Test Cave 1")
        self.assertEqual(str(trip), "Test Cave 1")

    def test_trip_get_absolute_url(self):
        """Test the Trip.get_absolute_url method"""
        trip = Trip.objects.get(cave_name="Test Cave 1")
        self.assertEqual(trip.get_absolute_url(), f"/trip/{trip.pk}/")

    def test_tidbits(self):
        """Test the Trip.tidbits property"""
        trip = Trip.objects.get(cave_name="Test Cave 6")
        tidbits = trip.tidbits

        expected_keys = [
            "Descended",
            "Climbed",
            "Distance",
            "Surveyed",
            "Aided",
            "Duration",
        ]

        self.assertEqual(len(tidbits), len(expected_keys))
        for k, v in tidbits:
            self.assertIn(k, expected_keys)

    def test_trip_index(self):
        """Test the Trip.trip_index class method"""
        trip = Trip.objects.get(cave_name="Test Cave 1")
        trip_index = Trip.trip_index(trip.user)
        self.assertEqual(len(trip_index), 6)
        self.assertEqual(trip_index[trip.pk], 1)

        trip = Trip.objects.get(cave_name="Test Cave 6")
        trip_index = Trip.trip_index(trip.user)
        self.assertEqual(trip_index[trip.pk], 6)

    def test_stats_for_user(self):
        """Test the Trip.stats_for_user class method"""
        user = get_user_model().objects.get(username="testusername")
        stats = Trip.stats_for_user(user)
        self.assertEqual(stats["trips"], 6)
        self.assertEqual(stats["vert_down"], D(m=100))
        self.assertEqual(stats["vert_up"], D(m=200))
        self.assertEqual(stats["horizontal"], D(m=300))
        self.assertEqual(stats["surveyed"], D(m=400))
        self.assertEqual(stats["aided"], D(m=500))
        self.assertEqual(stats["time"], "4 hours")

    def test_stats_for_user_with_no_trips(self):
        """Test the Trip.stats_for_user class method with no trips"""
        user = get_user_model().objects.create_user(
            email="test_no_trips@test.com",
            username="testusername2",
            password="testpassword",
            first_name="Joe",
            last_name="Bloggs",
        )
        stats = Trip.stats_for_user(user)
        self.assertEqual(stats["trips"], 0)
        self.assertEqual(stats["vert_down"], D(m=0))
        self.assertEqual(stats["vert_up"], D(m=0))
        self.assertEqual(stats["horizontal"], D(m=0))
        self.assertEqual(stats["surveyed"], D(m=0))
        self.assertEqual(stats["aided"], D(m=0))
        self.assertEqual(stats["time"], "0 minutes")
