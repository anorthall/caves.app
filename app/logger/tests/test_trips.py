import logging

from django.contrib.auth import get_user_model
from django.contrib.gis.measure import D
from django.core.exceptions import ValidationError
from django.test import Client, TestCase, tag
from django.urls import reverse
from django.utils import timezone as tz
from django.utils.timezone import datetime as dt
from django.utils.timezone import timedelta as td

from ..models import Trip, TripReport

User = get_user_model()


@tag("logger", "trip", "fast")
class TripModelTests(TestCase):
    def setUp(self):
        """Reduce log level to avoid 404 error"""
        logger = logging.getLogger("django.request")
        self.previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)

        # Test user to enable trip creation
        self.user = User.objects.create_user(
            email="test@test.com",
            username="testusername",
            password="password",
            name="Firstname",
        )
        self.user.is_active = True
        self.user.save()

        # Test user to test privacy settings
        self.user2 = User.objects.create(
            email="user2@caves.app",
            username="user2",
            password="password",
            name="User 2",
        )
        self.user2.is_active = True
        self.user2.save()

        # Trip with a start and end time
        self.trip = Trip.objects.create(
            user=self.user,
            cave_name="Duration Trip",
            start=dt.fromisoformat("2010-01-01T12:00:00+00:00"),
            end=dt.fromisoformat("2010-01-01T14:00:00+00:00"),
        )

        # Trip with no end time
        Trip.objects.create(
            user=self.user,
            cave_name="No Duration Trip",
            start=dt.fromisoformat("2010-01-01T13:00:00+00:00"),
        )

        # Private trip
        Trip.objects.create(
            user=self.user,
            cave_name="Private Trip",
            start=dt.fromisoformat("2010-01-01T14:00:00+00:00"),
            privacy=Trip.PRIVATE,
        )

        # Public trip
        Trip.objects.create(
            user=self.user,
            cave_name="Public Trip",
            start=dt.fromisoformat("2010-01-01T15:00:00+00:00"),
            privacy=Trip.PUBLIC,
        )

        # Default privacy trip
        Trip.objects.create(
            user=self.user,
            cave_name="Default Trip",
            start=dt.fromisoformat("2010-01-01T16:00:00+00:00"),
            privacy=Trip.DEFAULT,
        )

        # Trip with distances
        Trip.objects.create(
            user=self.user,
            cave_name="Distances Trip",
            start=dt.fromisoformat("2010-01-01T17:00:00+00:00"),
            end=dt.fromisoformat("2010-01-01T19:00:00+00:00"),
            vert_dist_down="100m",
            vert_dist_up="200m",
            horizontal_dist="300m",
            surveyed_dist="400m",
            resurveyed_dist="500m",
            aid_dist="600m",
        )

        # Trip report
        self.report = TripReport.objects.create(
            trip=self.trip,
            user=self.trip.user,
            title="Test Report",
            content="Test Report",
        )

    def tearDown(self):
        """Reset the log level back to normal"""
        logger = logging.getLogger("django.request")
        logger.setLevel(self.previous_level)

    def test_trip_duration(self):
        """
        Test that trip duration returns a timedelta with the correct value
        Test that trip duration returns None if no end time
        """
        trip_with_end = Trip.objects.get(cave_name="Duration Trip")
        trip_without_end = Trip.objects.get(cave_name="No Duration Trip")

        self.assertNotEqual(trip_with_end.end, None)
        self.assertEqual(trip_with_end.duration, td(hours=2))

        self.assertEqual(trip_without_end.end, None)
        self.assertEqual(trip_without_end.duration, None)

    def test_trip_duration_str(self):
        """Test that the trip duration string returns the correct value"""
        trip = Trip.objects.get(cave_name="Duration Trip")
        self.assertEqual(trip.duration_str, "2 hours")

        trip = Trip.objects.get(cave_name="Duration Trip")
        trip.end = dt.fromisoformat("2010-01-02T13:01:00+00:00")
        trip.save()
        self.assertEqual(trip.duration_str, "25 hours and 1 minute")

        trip = Trip.objects.get(cave_name="Duration Trip")
        trip.end = dt.fromisoformat("2010-01-03T14:02:00+00:00")
        trip.save()
        self.assertEqual(trip.duration_str, "50 hours and 2 minutes")

    def test_has_distances_property(self):
        """Test the Trip.has_distances property"""
        trip = Trip.objects.get(cave_name="Distances Trip")
        self.assertTrue(trip.has_distances)

        trip = Trip.objects.get(cave_name="Duration Trip")
        self.assertFalse(trip.has_distances)

    @tag("privacy")
    def test_trip_is_private_and_is_public(self):
        """Test the Trip.is_private and Trip.is_public functions"""
        trip_private = Trip.objects.get(cave_name="Private Trip")
        trip_public = Trip.objects.get(cave_name="Public Trip")
        trip_default = Trip.objects.get(cave_name="Default Trip")

        self.assertTrue(trip_private.is_private)
        self.assertFalse(trip_private.is_public)

        self.assertFalse(trip_public.is_private)
        self.assertTrue(trip_public.is_public)

        self.assertTrue(trip_default.is_private)
        self.assertFalse(trip_default.is_public)

    def test_trip_distance_validation(self):
        """Test the trip distance validation"""
        self.client.force_login(self.user)

        # Test above_zero_dist_validator()
        # Test vertical_dist_validator()
        response = self.client.post(
            reverse("log:trip_create"),
            {
                "cave_name": "Test Validation Cave",
                "type": Trip.SPORT,
                "start": tz.now(),
                "vert_dist_up": D(m=-100),
                "vert_dist_down": D(m=10000),
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Distance must be above zero")
        self.assertContains(response, "Distance is too large")

        # Test horizontal_dist_validator()
        response = self.client.post(
            reverse("log:trip_create"),
            {
                "cave_name": "Test Validation Cave",
                "type": Trip.SPORT,
                "start": tz.now(),
                "horizontal_dist": D(mi=30),
            },
        )
        self.assertContains(response, "Distance is too large")

    @tag("privacy")
    def test_trip_is_viewable_by_with_own_user(self):
        """Test the trip is_viewable_by function"""
        trip_private = Trip.objects.get(cave_name="Private Trip")
        trip_public = Trip.objects.get(cave_name="Public Trip")
        trip_default = Trip.objects.get(cave_name="Default Trip")

        self.assertTrue(trip_private.is_viewable_by(self.user))
        self.assertTrue(trip_public.is_viewable_by(self.user))
        self.assertTrue(trip_default.is_viewable_by(self.user))

    @tag("privacy")
    def test_trip_is_viewable_by_with_public_user(self):
        """Test the trip is_viewable_by function with a public user"""
        trip_private = Trip.objects.get(cave_name="Private Trip")
        trip_public = Trip.objects.get(cave_name="Public Trip")
        trip_default = Trip.objects.get(cave_name="Default Trip")

        self.user.privacy = User.PUBLIC
        self.user.save()
        self.assertFalse(trip_private.is_viewable_by(self.user2))
        self.assertTrue(trip_default.is_viewable_by(self.user2))
        self.assertTrue(trip_public.is_viewable_by(self.user2))

    @tag("privacy")
    def test_trip_is_viewable_by_with_private_user(self):
        """Test the trip is_viewable_by function with a private user"""
        trip_private = Trip.objects.get(cave_name="Private Trip")
        trip_public = Trip.objects.get(cave_name="Public Trip")
        trip_default = Trip.objects.get(cave_name="Default Trip")

        self.user.privacy = User.PRIVATE
        self.user.save()
        self.assertFalse(trip_private.is_viewable_by(self.user2))
        self.assertFalse(trip_default.is_viewable_by(self.user2))
        self.assertTrue(trip_public.is_viewable_by(self.user2))

    @tag("privacy")
    def test_trip_is_viewable_by_with_user_that_is_not_a_friend(self):
        """Test the trip is_viewable_by function with a non-friend user"""
        trip_private = Trip.objects.get(cave_name="Private Trip")
        trip_public = Trip.objects.get(cave_name="Public Trip")
        trip_default = Trip.objects.get(cave_name="Default Trip")

        self.user.privacy = User.FRIENDS
        self.user.save()
        self.assertFalse(trip_private.is_viewable_by(self.user2))
        self.assertFalse(trip_default.is_viewable_by(self.user2))
        self.assertTrue(trip_public.is_viewable_by(self.user2))

    @tag("privacy")
    def test_trip_is_viewable_by_with_user_that_is_a_friend(self):
        """Test the trip is_viewable_by function with a friend user"""
        trip_private = Trip.objects.get(cave_name="Private Trip")
        trip_public = Trip.objects.get(cave_name="Public Trip")
        trip_default = Trip.objects.get(cave_name="Default Trip")

        self.user.friends.add(self.user2)
        self.user2.friends.add(self.user)

        self.user.privacy = User.FRIENDS
        self.user.save()
        self.assertFalse(trip_private.is_viewable_by(self.user2))
        self.assertTrue(trip_default.is_viewable_by(self.user2))
        self.assertTrue(trip_public.is_viewable_by(self.user2))

        trip_friends = trip_default
        trip_friends.privacy = Trip.FRIENDS
        trip_friends.save()
        self.assertTrue(trip_friends.is_viewable_by(self.user2))

    @tag("privacy")
    def test_trip_report_is_private_and_is_public(self):
        """Test the trip report is_private and is_public functions"""
        self.trip.privacy = Trip.PRIVATE
        self.trip.save()

        self.report.privacy = TripReport.DEFAULT
        self.report.save()

        self.assertEqual(self.report.trip, self.trip)
        self.assertTrue(self.report.is_private)
        self.assertFalse(self.report.is_public)

        self.report.privacy = TripReport.PRIVATE
        self.report.save()
        self.assertTrue(self.report.is_private)
        self.assertFalse(self.report.is_public)

        self.report.privacy = TripReport.PUBLIC
        self.report.save()
        self.assertFalse(self.report.is_private)
        self.assertTrue(self.report.is_public)

    def test_trip_str(self):
        """Test the Trip model __str__ function"""
        self.assertEqual(str(self.trip), self.trip.cave_name)

    def test_trip_report_str(self):
        """Test the TripReport model __str__ function"""
        self.assertEqual(str(self.report), self.report.title)

    def test_trip_validates_start_time_before_end_time(self):
        """Test the Trip model validates start time before end time"""
        self.trip.start = tz.now() + td(days=1)
        self.trip.end = tz.now()
        with self.assertRaises(ValidationError):
            self.trip.full_clean()

    def test_build_liked_str_function(self):
        """Test the build_liked_str function"""
        result = self.trip._build_liked_str(["you"], True)
        self.assertEqual(result, "You liked this")

        result = self.trip._build_liked_str(["Andrew"], False)
        self.assertEqual(result, "Andrew liked this")

        result = self.trip._build_liked_str(["Andrew", "you"], True)
        self.assertEqual(result, "Liked by Andrew and you")

        result = self.trip._build_liked_str(["Andrew", "Bob", "you"], True)
        self.assertEqual(result, "Liked by Andrew, Bob and you")

        result = self.trip._build_liked_str(["Andrew", "Bob", "Charlie"], False)
        self.assertEqual(result, "Liked by Andrew, Bob and 1 other")

        result = self.trip._build_liked_str(["Andrew", "Bob", "Charlie", "Dave"], False)
        self.assertEqual(result, "Liked by Andrew, Bob and 2 others")

        result = self.trip._build_liked_str(
            ["Andrew", "Bob", "Charlie", "Dave", "you"], True
        )
        self.assertEqual(result, "Liked by Andrew, Bob and 3 others")

        result = self.trip._build_liked_str(
            ["Andrew", "Bob", "Charlie", "Dave", "you"], True, 1
        )
        self.assertEqual(result, "Liked by Andrew and 4 others")

        with self.assertRaises(ValueError):
            self.trip._build_liked_str([], True, 0)

    def test_trip_has_distances_function(self):
        """Test the Trip model has_distances function"""
        t = self.trip
        self.assertFalse(t.has_distances)

        t.horizontal_dist = "1m"
        self.assertTrue(self.trip.has_distances)

        t.horizontal_dist = "0m"
        t.vert_dist_up = "1m"
        self.assertTrue(self.trip.has_distances)

        t.vert_dist_up = "0m"
        t.vert_dist_down = "1m"
        self.assertTrue(self.trip.has_distances)

        t.vert_dist_down = "0m"
        t.aid_dist = "1m"
        self.assertTrue(self.trip.has_distances)

        t.aid_dist = "0m"
        t.surveyed_dist = "1m"
        self.assertTrue(self.trip.has_distances)

        t.surveyed_dist = "0m"
        t.resurveyed_dist = "1m"
        self.assertTrue(self.trip.has_distances)

    def test_friends_appear_first_in_liked_str(self):
        """Test that friends appear first in the liked string"""
        # Create 10 users
        users = []
        for i in range(10):
            u = User.objects.create_user(
                email=f"test_user{i}@user.app",
                username=f"test_user{i}",
                password="password",
                name=f"Test User {i}",
            )
            users.append(u)
            self.trip.likes.add(u)

        user4, user5 = users[4], users[5]

        user4.friends.add(self.user)
        self.user.friends.add(user4)

        user5.friends.add(self.user)
        self.user.friends.add(user5)

        result = self.trip.get_liked_str(self.user, self.user.friends.all())
        self.assertEqual(result, "Liked by Test User 4, Test User 5 and 8 others")

    def test_trip_number_function(self):
        """Test the Trip model number function"""
        self.assertEqual(self.trip.number, 1)
        self.trip.start = tz.now()
        self.trip.save()
        self.assertEqual(self.trip.number, 6)

    @tag("views")
    def test_trip_creation_form(self):
        """Test the trip creation form"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("log:trip_create"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Add a trip")
        self.assertContains(response, "Cave name")
        self.assertContains(response, "Region")
        self.assertContains(response, "Country")
        self.assertContains(response, "Cavers")
        self.assertContains(response, "Trip notes")
        self.assertContains(response, "Create trip")

        response = self.client.post(
            reverse("log:trip_create"),
            {
                "cave_name": "Test The Form Cave",
                "cave_region": "Test Region",
                "cave_country": "Test Country",
                "type": Trip.SPORT,
                "cavers": "Test Cavers",
                "start": tz.now(),
                "end": tz.now() + td(days=1),
                "privacy": Trip.DEFAULT,
                "notes": "Test Notes",
            },
        )
        trip = Trip.objects.get(cave_name="Test The Form Cave")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, trip.get_absolute_url())
        self.assertEqual(trip.cave_name, "Test The Form Cave")
        self.assertEqual(trip.cave_region, "Test Region")
        self.assertEqual(trip.cave_country, "Test Country")
        self.assertEqual(trip.type, Trip.SPORT)
        self.assertEqual(trip.cavers, "Test Cavers")
        self.assertEqual(trip.notes, "Test Notes")
        self.assertEqual(trip.privacy, Trip.DEFAULT)

    @tag("views")
    def test_trip_creation_form_with_invalid_data(self):
        """Test the trip creation form with invalid data"""
        self.client.force_login(self.user)
        response = self.client.post(reverse("log:trip_create"), {})
        self.assertContains(response, "This field is required.")

        response = self.client.post(
            reverse("log:trip_create"),
            {
                "cave_name": "Test The Form Cave",
                "start": tz.now(),
                "end": tz.now() - td(days=1),
            },
        )
        self.assertContains(
            response, "The trip start time must be before " "the trip end time."
        )

        response = self.client.post(
            reverse("log:trip_create"),
            {
                "cave_name": "Test The Form Cave",
                "start": tz.now() - td(days=100),
                "end": tz.now(),
            },
        )
        self.assertContains(response, "The trip is unrealistically long")

        same_time = tz.now()
        response = self.client.post(
            reverse("log:trip_create"),
            {
                "cave_name": "Test The Form Cave",
                "cave_region": "Test Region",
                "cave_country": "Test Country",
                "type": Trip.SPORT,
                "cavers": "Test Cavers",
                "privacy": Trip.DEFAULT,
                "notes": "Test Notes",
                "start": same_time,
                "end": same_time,
            },
        )
        self.assertContains(response, "The start and end time must not be the same")

        response = self.client.post(
            reverse("log:trip_create"),
            {
                "cave_name": "Test The Form Cave",
                "cave_region": "Test Region",
                "cave_country": "Test Country",
                "type": Trip.SPORT,
                "cavers": "Test Cavers",
                "privacy": Trip.DEFAULT,
                "notes": "Test Notes",
                "start": tz.now() + td(days=8),
                "end": tz.now(),
            },
        )
        self.assertContains(
            response, "Trips must not start more than one week in the future"
        )

        response = self.client.post(
            reverse("log:trip_create"),
            {
                "cave_name": "Test The Form Cave",
                "cave_region": "Test Region",
                "cave_country": "Test Country",
                "type": Trip.SPORT,
                "cavers": "Test Cavers",
                "privacy": Trip.DEFAULT,
                "notes": "Test Notes",
                "start": tz.now(),
                "end": tz.now() + td(days=32),
            },
        )
        self.assertContains(
            response, "Trips must not end more than 31 days in the future"
        )

    @tag("views")
    def test_trip_create_form_addanother_function(self):
        """Test the trip creation form add another function"""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("log:trip_create"),
            {
                "cave_name": "Test The Form Cave",
                "type": Trip.SPORT,
                "privacy": Trip.DEFAULT,
                "start": tz.now(),
                "addanother": True,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("log:trip_create"))

    # TODO: Test trip update form with invalid user
    @tag("views")
    def test_trip_update_form(self):
        """Test the trip update form"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("log:trip_update", args=[self.trip.uuid]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Edit trip")
        self.assertContains(response, "Cave name")
        self.assertContains(response, "Region")
        self.assertContains(response, "Country")
        self.assertContains(response, "Cavers")
        self.assertContains(response, "Trip notes")
        self.assertContains(response, "Update trip")
        self.assertContains(response, self.trip.cave_name)

        response = self.client.post(
            reverse("log:trip_update", args=[self.trip.uuid]),
            {
                "cave_name": "Test The Form Cave",
                "cave_region": "Test Region",
                "cave_country": "Test Country",
                "type": Trip.SPORT,
                "cavers": "Test Cavers",
                "start": tz.now(),
                "end": tz.now() + td(days=1),
                "privacy": Trip.DEFAULT,
                "notes": "Test Notes",
            },
        )
        trip = Trip.objects.get(pk=self.trip.pk)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, trip.get_absolute_url())
        self.assertEqual(trip.cave_name, "Test The Form Cave")
        self.assertEqual(trip.cave_region, "Test Region")
        self.assertEqual(trip.cave_country, "Test Country")
        self.assertEqual(trip.type, Trip.SPORT)
        self.assertEqual(trip.cavers, "Test Cavers")
        self.assertEqual(trip.notes, "Test Notes")
        self.assertEqual(trip.privacy, Trip.DEFAULT)
        self.assertEqual(trip.user, self.user)

    @tag("views")
    def test_trip_delete_view(self):
        """Test the trip delete view"""
        self.client.force_login(self.user)

        trip_pk = self.trip.pk
        success_str = f"The trip to {self.trip.cave_name} has been deleted"

        response = self.client.post(
            reverse("log:trip_delete", args=[self.trip.uuid]), follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, success_str)
        self.assertFalse(Trip.objects.filter(pk=trip_pk).exists())

    @tag("privacy", "views")
    def test_trip_delete_view_as_incorrect_user(self):
        """Test the trip delete view as an incorrect user"""
        self.client.force_login(self.user2)
        response = self.client.post(
            reverse("log:trip_delete", args=[self.trip.uuid]),
        )
        self.assertEqual(response.status_code, 403)


@tag("logger", "fast", "trip", "views")
class TripDetailViewTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.user = User.objects.create_user(
            email="user@caves.app",
            username="user",
            password="password",
            name="User Name",
        )
        self.user.is_active = True
        self.user.privacy = User.PUBLIC
        self.user.save()

        self.user2 = User.objects.create_user(
            email="user2@caves.app",
            username="user2",
            password="password",
            name="User 2 Name",
        )
        self.user2.is_active = True
        self.user2.privacy = User.PUBLIC
        self.user2.save()

        for i in range(1, 200):
            Trip.objects.create(
                cave_name=f"User1 Cave {i}",
                start=tz.now() - td(days=i),
                user=self.user,
                notes="User1 trip notes",
            )

        for i in range(1, 200):
            Trip.objects.create(
                cave_name=f"User2 Cave {i}",
                start=tz.now() - td(days=i),
                user=self.user2,
                notes="User2 trip notes",
            )

    @tag("privacy")
    def test_trip_detail_page_with_various_privacy_settings(self):
        """Test the trip detail page with various privacy settings"""
        trip = self.user.trips.first()
        trip.privacy = Trip.PUBLIC
        trip.save()

        self.client.force_login(self.user2)
        response = self.client.get(trip.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, trip.cave_name)

        trip.privacy = Trip.FRIENDS
        trip.save()
        response = self.client.get(trip.get_absolute_url())
        self.assertEqual(response.status_code, 403)

        self.user.friends.add(self.user2)
        self.user2.friends.add(self.user)
        response = self.client.get(trip.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, trip.cave_name)

        trip.privacy = Trip.PRIVATE
        trip.save()
        response = self.client.get(trip.get_absolute_url())
        self.assertEqual(response.status_code, 403)

        trip.privacy = Trip.DEFAULT
        trip.save()
        self.user.privacy = User.PRIVATE
        self.user.save()
        response = self.client.get(trip.get_absolute_url())
        self.assertEqual(response.status_code, 403)

        self.user.privacy = User.PUBLIC
        self.user.save()
        response = self.client.get(trip.get_absolute_url())
        self.assertEqual(response.status_code, 200)

        self.user.privacy = User.FRIENDS
        self.user.save()
        response = self.client.get(trip.get_absolute_url())
        self.assertContains(response, trip.cave_name)

        self.user.privacy = User.PUBLIC
        self.user.save()
        response = self.client.get(trip.get_absolute_url())
        self.assertContains(response, trip.cave_name)

        self.client.logout()
        response = self.client.get(trip.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, trip.cave_name)

        self.user.privacy = User.FRIENDS
        self.user.save()
        response = self.client.get(trip.get_absolute_url())
        self.assertEqual(response.status_code, 403)

        self.user.privacy = User.PRIVATE
        self.user.save()
        response = self.client.get(trip.get_absolute_url())
        self.assertEqual(response.status_code, 403)

    def test_sidebar_displays_properly_when_viewing_another_users_trip(self):
        """Test that the sidebar displays properly when viewing another user's trip"""
        self.client.force_login(self.user2)
        trip = Trip.objects.filter(user=self.user).first()
        response = self.client.get(trip.get_absolute_url())
        self.assertContains(response, trip.cave_name)
        self.assertContains(response, "User profile")
        self.assertContains(response, "View trip")
        self.assertContains(response, "Add as friend")

        self.assertNotContains(response, reverse("log:trip_update", args=[trip.uuid]))
        self.assertNotContains(response, reverse("log:trip_delete", args=[trip.uuid]))
        self.assertNotContains(response, reverse("log:report_create", args=[trip.uuid]))

    @tag("privacy")
    def test_add_as_friend_link_does_not_appear_when_disabled(self):
        """Test that the add as friend link does not appear when disabled"""
        self.user.allow_friend_username = False
        self.user.save()

        self.client.force_login(self.user2)
        trip = Trip.objects.filter(user=self.user).first()
        response = self.client.get(trip.get_absolute_url())
        self.assertNotContains(response, "Add as friend")
        self.assertNotContains(response, reverse("users:friend_add"))

    def test_add_as_friend_link_does_not_appear_when_already_friends(self):
        """Test that the add as friend link does not appear when already friends"""
        self.user.friends.add(self.user2)
        self.user2.friends.add(self.user)

        self.client.force_login(self.user2)
        trip = Trip.objects.filter(user=self.user).first()
        response = self.client.get(trip.get_absolute_url())
        self.assertNotContains(response, "Add as friend")
        self.assertNotContains(response, reverse("users:friend_add"))

    def test_trip_report_link_appears_in_sidebar_for_other_users(self):
        """Test that the trip report link appears in the sidebar for other users"""
        trip = Trip.objects.filter(user=self.user).first()
        report = TripReport.objects.create(
            user=self.user,
            trip=trip,
            title="Test report",
            content="Test report content",
        )
        response = self.client.get(trip.get_absolute_url())
        self.assertContains(response, report.get_absolute_url())

    @tag("privacy")
    def test_trip_report_link_does_not_appear_in_sidebar_when_private(self):
        """Test that the trip report link does not appear in the sidebar when private"""
        trip = Trip.objects.filter(user=self.user).first()

        report = TripReport.objects.create(
            user=self.user,
            trip=trip,
            title="Test report",
            content="Test report content",
            privacy=TripReport.PRIVATE,
        )
        response = self.client.get(trip.get_absolute_url())
        self.assertNotContains(response, report.get_absolute_url())
