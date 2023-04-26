import logging

from django.contrib import auth
from django.contrib.auth import get_user_model
from django.contrib.gis.measure import D
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.test import Client, TestCase, tag
from django.urls import reverse
from django.utils import timezone as tz
from django.utils.timezone import datetime as dt
from django.utils.timezone import timedelta as td
from users.models import Notification, UserSettings

from .models import Comment, Trip, TripReport
from .templatetags import distformat

User = get_user_model()


@tag("logger", "trip", "fast", "unit")
class TripModelUnitTests(TestCase):
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

        Trip.objects.create(
            user=self.user,
            cave_name="Private Trip",
            start=dt.fromisoformat("2010-01-01T14:00:00+00:00"),
            privacy=Trip.PRIVATE,
        )
        Trip.objects.create(
            user=self.user,
            cave_name="Public Trip",
            start=dt.fromisoformat("2010-01-01T15:00:00+00:00"),
            privacy=Trip.PUBLIC,
        )
        Trip.objects.create(
            user=self.user,
            cave_name="Default Trip",
            start=dt.fromisoformat("2010-01-01T16:00:00+00:00"),
            privacy=Trip.DEFAULT,
        )

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

        self.report = TripReport.objects.create(
            trip=self.trip,
            user=self.trip.user,
            title="Test Report",
            pub_date=tz.now(),
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
        self.assertEqual(trip.duration_str, "1 day, 1 hour and 1 minute")

        trip = Trip.objects.get(cave_name="Duration Trip")
        trip.end = dt.fromisoformat("2010-01-03T14:02:00+00:00")
        trip.save()
        self.assertEqual(trip.duration_str, "2 days, 2 hours and 2 minutes")

    def test_has_distances_property(self):
        """Test the Trip.has_distances property"""
        trip = Trip.objects.get(cave_name="Distances Trip")
        self.assertTrue(trip.has_distances)

        trip = Trip.objects.get(cave_name="Duration Trip")
        self.assertFalse(trip.has_distances)

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

    def test_trip_is_viewable_by_with_own_user(self):
        """Test the trip is_viewable_by function"""
        trip_private = Trip.objects.get(cave_name="Private Trip")
        trip_public = Trip.objects.get(cave_name="Public Trip")
        trip_default = Trip.objects.get(cave_name="Default Trip")

        self.assertTrue(trip_private.is_viewable_by(self.user))
        self.assertTrue(trip_public.is_viewable_by(self.user))
        self.assertTrue(trip_default.is_viewable_by(self.user))

    def test_trip_is_viewable_by_with_public_user(self):
        """Test the trip is_viewable_by function with a public user"""
        trip_private = Trip.objects.get(cave_name="Private Trip")
        trip_public = Trip.objects.get(cave_name="Public Trip")
        trip_default = Trip.objects.get(cave_name="Default Trip")

        self.user.settings.privacy = UserSettings.PUBLIC
        self.user.settings.save()
        self.assertFalse(trip_private.is_viewable_by(self.user2))
        self.assertTrue(trip_default.is_viewable_by(self.user2))
        self.assertTrue(trip_public.is_viewable_by(self.user2))

    def test_trip_is_viewable_by_with_private_user(self):
        """Test the trip is_viewable_by function with a private user"""
        trip_private = Trip.objects.get(cave_name="Private Trip")
        trip_public = Trip.objects.get(cave_name="Public Trip")
        trip_default = Trip.objects.get(cave_name="Default Trip")

        self.user.settings.privacy = UserSettings.PRIVATE
        self.user.settings.save()
        self.assertFalse(trip_private.is_viewable_by(self.user2))
        self.assertFalse(trip_default.is_viewable_by(self.user2))
        self.assertTrue(trip_public.is_viewable_by(self.user2))

    def test_trip_is_viewable_by_with_user_that_is_not_a_friend(self):
        """Test the trip is_viewable_by function with a non-friend user"""
        trip_private = Trip.objects.get(cave_name="Private Trip")
        trip_public = Trip.objects.get(cave_name="Public Trip")
        trip_default = Trip.objects.get(cave_name="Default Trip")

        self.user.settings.privacy = UserSettings.FRIENDS
        self.user.settings.save()
        self.assertFalse(trip_private.is_viewable_by(self.user2))
        self.assertFalse(trip_default.is_viewable_by(self.user2))
        self.assertTrue(trip_public.is_viewable_by(self.user2))

    def test_trip_is_viewable_by_with_user_that_is_a_friend(self):
        """Test the trip is_viewable_by function with a friend user"""
        trip_private = Trip.objects.get(cave_name="Private Trip")
        trip_public = Trip.objects.get(cave_name="Public Trip")
        trip_default = Trip.objects.get(cave_name="Default Trip")

        self.user.profile.friends.add(self.user2)
        self.user2.profile.friends.add(self.user)

        self.user.settings.privacy = UserSettings.FRIENDS
        self.user.settings.save()
        self.assertFalse(trip_private.is_viewable_by(self.user2))
        self.assertTrue(trip_default.is_viewable_by(self.user2))
        self.assertTrue(trip_public.is_viewable_by(self.user2))

        trip_friends = trip_default
        trip_friends.privacy = Trip.FRIENDS
        trip_friends.save()
        self.assertTrue(trip_friends.is_viewable_by(self.user2))

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

    def test_comment_str(self):
        """Test the Comment model __str__ function"""
        c = Comment.objects.create(
            author=self.user, content_object=self.trip, content="This is a comment"
        )
        self.assertEqual(str(c), f"Comment by {c.author} on {c.content_object}")

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

        result = self.trip._build_liked_str(["Andrew", "you"], True)
        self.assertEqual(result, "Liked by Andrew, and you")

        result = self.trip._build_liked_str(["Andrew", "Bob", "you"], True)
        self.assertEqual(result, "Liked by Andrew, Bob, and you")

        result = self.trip._build_liked_str(["Andrew", "Bob", "Charlie"], False)
        self.assertEqual(result, "Liked by Andrew, Bob, and 1 other")

        result = self.trip._build_liked_str(["Andrew", "Bob", "Charlie", "Dave"], False)
        self.assertEqual(result, "Liked by Andrew, Bob, and 2 others")

        result = self.trip._build_liked_str(
            ["Andrew", "Bob", "Charlie", "Dave", "you"], True
        )
        self.assertEqual(result, "Liked by Andrew, Bob, and 3 others")

        result = self.trip._build_liked_str(
            ["Andrew", "Bob", "Charlie", "Dave", "you"], True, 1
        )
        self.assertEqual(result, "Liked by Andrew, and 4 others")

        with self.assertRaises(ValueError):
            result = self.trip._build_liked_str([], True, 0)

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

        user4.profile.friends.add(self.user)
        self.user.profile.friends.add(user4)

        user5.profile.friends.add(self.user)
        self.user.profile.friends.add(user5)

        result = self.trip.get_liked_str(self.user, self.user.profile.friends.all())
        self.assertEqual(result, "Liked by Test User 4, Test User 5, and 8 others")

    def test_trip_number_function(self):
        """Test the Trip model number function"""
        self.assertEqual(self.trip.number, 1)
        self.trip.start = tz.now()
        self.trip.save()
        self.assertEqual(self.trip.number, 6)


@tag("logger", "trip", "fast", "integration")
class TripIntegrationTests(TestCase):
    def setUp(self):
        """Reduce log level to avoid 404 error"""
        logger = logging.getLogger("django.request")
        self.previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)

        self.client = Client()
        self.user = User.objects.create_user(
            email="enabled@user.app",
            username="enabled",
            password="testpassword",
            name="Joe",
        )
        self.user.is_active = True
        self.user.save()
        self.trip = Trip.objects.create(
            user=self.user,
            cave_name="Test Cave",
            start=tz.now() - td(days=1),
            end=tz.now(),
        )

    def tearDown(self):
        """Reset the log level back to normal"""
        logger = logging.getLogger("django.request")
        logger.setLevel(self.previous_level)

    def test_non_superuser_cannot_access_admin_tools(self):
        """Test that a non-superuser cannot access the admin tools"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("log:admin_tools"))
        self.assertEqual(response.status_code, 404)

    def test_trip_list_view(self):
        """Test the trip list view"""
        self.client.force_login(self.user)

        # Create 50 trips with randomised names
        from random import random

        trips = []
        for i in range(50):
            trips.append(
                Trip(
                    user=self.user,
                    cave_name="Test Cave " + str(random()),
                    start=tz.now(),
                )
            )
        Trip.objects.bulk_create(trips)

        response = self.client.get(reverse("log:user", args=[self.user.username]))
        self.assertEqual(response.status_code, 200)
        for trip in trips:
            self.assertContains(response, trip.cave_name)

    def test_trip_creation_form(self):
        """Test the trip creation form"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("log:trip_create"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Add a trip")
        self.assertContains(response, "Cave name")
        self.assertContains(response, "Cave region")
        self.assertContains(response, "Cave country")
        self.assertContains(response, "Cavers")
        self.assertContains(response, "Notes")
        self.assertContains(response, "Save")

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
        self.assertEqual(response.url, f"/trip/{trip.pk}/")
        self.assertEqual(trip.cave_name, "Test The Form Cave")
        self.assertEqual(trip.cave_region, "Test Region")
        self.assertEqual(trip.cave_country, "Test Country")
        self.assertEqual(trip.type, Trip.SPORT)
        self.assertEqual(trip.cavers, "Test Cavers")
        self.assertEqual(trip.notes, "Test Notes")
        self.assertEqual(trip.privacy, Trip.DEFAULT)

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

    def test_trip_update_form(self):
        """Test the trip update form"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("log:trip_update", args=[self.trip.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Edit trip")
        self.assertContains(response, "Cave name")
        self.assertContains(response, "Cave region")
        self.assertContains(response, "Cave country")
        self.assertContains(response, "Cavers")
        self.assertContains(response, "Notes")
        self.assertContains(response, "Save")
        self.assertContains(response, self.trip.cave_name)

        response = self.client.post(
            reverse("log:trip_update", args=[self.trip.pk]),
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
        self.assertEqual(response.url, f"/trip/{trip.pk}/")
        self.assertEqual(trip.cave_name, "Test The Form Cave")
        self.assertEqual(trip.cave_region, "Test Region")
        self.assertEqual(trip.cave_country, "Test Country")
        self.assertEqual(trip.type, Trip.SPORT)
        self.assertEqual(trip.cavers, "Test Cavers")
        self.assertEqual(trip.notes, "Test Notes")
        self.assertEqual(trip.privacy, Trip.DEFAULT)
        self.assertEqual(trip.user, self.user)

    def test_trip_delete_view(self):
        """Test the trip delete view"""
        self.client.force_login(self.user)

        trip_pk = self.trip.pk
        success_str = f"The trip to {self.trip.cave_name} has been deleted"

        response = self.client.get(
            reverse("log:trip_delete", args=[self.trip.pk]), follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, success_str)
        self.assertFalse(Trip.objects.filter(pk=trip_pk).exists())

    def test_trip_delete_view_as_incorrect_user(self):
        """Test the trip delete view as an incorrect user"""
        user2 = User.objects.create_user(
            email="user2@caves.app",
            username="user2",
            password="password",
            name="User 2",
        )
        user2.is_active = True
        user2.save()
        self.client.force_login(user2)
        response = self.client.get(
            reverse("log:trip_delete", args=[self.trip.pk]),
        )
        self.assertEqual(response.status_code, 404)


@tag("logger", "tripreport", "fast", "integration")
class TripReportIntegrationTests(TestCase):
    def setUp(self):
        """Reduce log level to avoid 404 error"""
        logger = logging.getLogger("django.request")
        self.previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)

        # Create an enabled user
        self.user = User.objects.create_user(
            email="enabled@user.app",
            username="enabled",
            password="testpassword",
            name="Joe",
        )
        self.user.is_active = True
        self.user.save()

        self.trip = Trip.objects.create(
            user=self.user,
            cave_name="Test Cave",
            start=tz.now(),
        )

    def tearDown(self):
        """Reset the log level back to normal"""
        logger = logging.getLogger("django.request")
        logger.setLevel(self.previous_level)

    def test_slug_is_unique_for_user_only(self):
        """Test that the slug is unique for the user only"""
        TripReport.objects.create(
            user=self.user,
            trip=self.trip,
            title="Test Report",
            slug="slug",
            content="Test Content",
            pub_date=tz.now().date(),
        )

        # Create another user, trip, and trip report with the same slug.
        user2 = User.objects.create_user(
            email="test2@users.app",
            username="username2",
            password="password2",
            name="Test2",
        )
        trip2 = Trip.objects.create(
            user=user2,
            cave_name="No Duration Trip",
            start=tz.now(),
        )
        TripReport.objects.create(
            user=user2,
            trip=trip2,
            title="Test Report 2",
            slug="slug",
            content="Test Content 2",
            pub_date=tz.now().date(),
        )

        # Now create a second trip/report for the original user with the same slug
        with self.assertRaises(IntegrityError):
            trip = Trip.objects.create(
                user=self.user,
                cave_name="Test Cave",
                start=tz.now(),
            )
            TripReport.objects.create(
                user=self.user,
                trip=trip,
                title="Test Report",
                slug="slug",
                content="Test Content",
                pub_date=tz.now().date(),
            )

    def test_trip_report_create_view(self):
        """Test the trip report create view in GET and POST"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("log:report_create", args=[self.trip.pk]))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse("log:report_create", args=[self.trip.pk]),
            {
                "title": "Test Report",
                "pub_date": dt.now().date(),
                "slug": "test-report",
                "content": "Test content.",
                "privacy": TripReport.PUBLIC,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, reverse("log:report_detail", args=[self.trip.pk])
        )
        self.assertEqual(TripReport.objects.count(), 1)
        self.assertEqual(TripReport.objects.get().title, "Test Report")
        self.assertEqual(TripReport.objects.get().content, "Test content.")
        self.assertEqual(TripReport.objects.get().privacy, TripReport.PUBLIC)
        self.assertEqual(TripReport.objects.get().trip, self.trip)

    def test_trip_report_create_view_with_a_duplicate_slug(self):
        """Test the trip report create view with a duplicate slug"""
        TripReport.objects.create(
            title="Test Report",
            pub_date=dt.now().date(),
            slug="test-report",
            content="Test content.",
            trip=self.trip,
            user=self.user,
        )

        trip = Trip.objects.create(
            user=self.user,
            cave_name="Test Cave",
            start=tz.now(),
        )

        self.client.force_login(self.user)
        response = self.client.post(
            reverse("log:report_create", args=[trip.pk]),
            {
                "title": "Test Report",
                "pub_date": dt.now().date(),
                "slug": "test-report",
                "content": "Test content.",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The slug must be unique.")

    def test_trip_report_create_view_redirects_if_a_report_already_exists(self):
        """Test the trip report create view redirects if a report already exists"""
        report = TripReport.objects.create(
            title="Test Report",
            pub_date=dt.now().date(),
            slug="test-report",
            content="Test content.",
            privacy=TripReport.PUBLIC,
            trip=self.trip,
            user=self.user,
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse("log:report_create", args=[report.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("log:report_detail", args=[report.pk]))

    def test_users_cannot_edit_a_trip_report_for_other_users(self):
        """Test users cannot edit a trip report which does not belong to them."""
        user = User.objects.create_user(
            email="new@user.app",
            password="password",
            username="testuser",
            name="Test",
        )
        user.is_active = True
        user.save()

        report = TripReport.objects.create(
            title="Test Report",
            pub_date=dt.now().date(),
            slug="test-report",
            content="Test content.",
            privacy=TripReport.PUBLIC,
            trip=self.trip,
            user=self.user,
        )

        self.client.login(email="new@user.app", password="password")
        response = self.client.get(reverse("log:report_update", args=[report.pk]))
        self.assertEqual(response.status_code, 404)

        response = self.client.get(reverse("log:report_delete", args=[report.pk]))
        self.assertEqual(response.status_code, 404)

        response = self.client.get(reverse("log:report_create", args=[self.trip.pk]))
        self.assertEqual(response.status_code, 404)

    def test_users_can_view_and_edit_their_own_trip_reports(self):
        """Test users can view and edit their own trip reports."""
        report = TripReport.objects.create(
            title="Test Report",
            pub_date=dt.now().date(),
            slug="test-report",
            content="Test content.",
            privacy=TripReport.PUBLIC,
            trip=self.trip,
            user=self.user,
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse("log:report_detail", args=[report.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Report")
        self.assertContains(response, "Test content.")

        response = self.client.get(reverse("log:report_update", args=[report.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Report")
        self.assertContains(response, "Test content.")

        response = self.client.post(
            reverse("log:report_update", args=[report.pk]),
            {
                "title": "Test Report Updated",
                "pub_date": dt.now().date(),
                "slug": "test-report",
                "content": "Test content updated.",
                "privacy": TripReport.PUBLIC,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("log:report_detail", args=[report.pk]))

        report.refresh_from_db()
        self.assertEqual(report.title, "Test Report Updated")
        self.assertEqual(report.slug, "test-report")
        self.assertEqual(report.content, "Test content updated.")

        response = self.client.get(reverse("log:report_delete", args=[report.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("log:trip_detail", args=[self.trip.pk]))
        self.assertEqual(TripReport.objects.count(), 0)

    def test_trip_report_link_appears_on_trip_list(self):
        """Test the trip report link appears on the trip list page."""
        self.client.force_login(self.user)
        report = TripReport.objects.create(
            title="Test Report",
            pub_date=dt.now().date(),
            slug="test-report",
            content="Test content.",
            privacy=TripReport.PUBLIC,
            trip=self.trip,
            user=self.user,
        )

        response = self.client.get(reverse("log:user", args=[self.user.username]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("log:report_detail", args=[report.pk]))

    def test_trip_report_link_appears_on_trip_detail(self):
        """Test the trip report link appears on the trip detail page"""
        self.client.force_login(self.user)
        report = TripReport.objects.create(
            title="Test Report",
            pub_date=dt.now().date(),
            slug="test-report",
            content="Test content.",
            privacy=TripReport.PUBLIC,
            trip=self.trip,
            user=self.user,
        )

        response = self.client.get(reverse("log:trip_detail", args=[self.trip.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("log:report_detail", args=[report.pk]))

    def test_add_trip_report_link_appears_when_no_report_has_been_added(self):
        """Test the add trip report link appears on the trip detail page"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("log:trip_detail", args=[self.trip.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("log:report_create", args=[self.trip.pk]))

    def test_add_trip_report_does_not_appear_when_report_added(self):
        """Test the add trip report link does not appear on the detail page"""
        self.client.force_login(self.user)
        TripReport.objects.create(
            title="Test Report",
            pub_date=dt.now().date(),
            slug="test-report",
            content="Test content.",
            privacy=TripReport.PUBLIC,
            trip=self.trip,
            user=self.user,
        )

        response = self.client.get(reverse("log:trip_detail", args=[self.trip.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(
            response, reverse("log:report_create", args=[self.trip.pk])
        )

    def test_view_and_edit_trip_report_links_appear_when_a_report_has_been_added(self):
        """Test the view and edit trip report links appear on the trip detail page"""
        self.client.force_login(self.user)
        report = TripReport.objects.create(
            title="Test Report",
            pub_date=dt.now().date(),
            slug="test-report",
            content="Test content.",
            privacy=TripReport.PUBLIC,
            trip=self.trip,
            user=self.user,
        )

        response = self.client.get(reverse("log:trip_detail", args=[self.trip.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("log:report_detail", args=[report.pk]))
        self.assertContains(response, reverse("log:report_update", args=[report.pk]))


@tag("integration", "fast", "social")
class SocialFunctionalityIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.user = User.objects.create_user(
            email="user@caves.app",
            username="user",
            password="password",
            name="User Name",
        )
        self.user.is_active = True
        self.user.save()
        self.user.settings.privacy = UserSettings.PUBLIC
        self.user.settings.save()

        self.user2 = User.objects.create_user(
            email="user2@caves.app",
            username="user2",
            password="password",
            name="User 2 Name",
        )
        self.user2.is_active = True
        self.user2.save()
        self.user2.settings.privacy = UserSettings.PUBLIC
        self.user2.settings.save()

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

    def test_user_profile_page_trip_list(self):
        """Test the trip list on the user profile page"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("log:user", args=[self.user.username]))
        self.assertEqual(response.status_code, 200)

        # Test pagination and that the correct trips are displayed
        for i in range(1, 50):
            self.assertContains(response, f"User1 Cave {i}")
            self.assertNotContains(response, f"User2 Cave {i}")

        for i in range(51, 100):
            self.assertNotContains(response, f"User1 Cave {i}")
            self.assertNotContains(response, f"User2 Cave {i}")

        # Test edit links appear
        for trip in self.user.trips.order_by("-start")[:50]:
            self.assertContains(response, reverse("log:trip_update", args=[trip.pk]))

        # Test the next page
        response = self.client.get(
            reverse("log:user", args=[self.user.username]) + "?page=2",
        )
        self.assertEqual(response.status_code, 200)
        for i in range(51, 100):
            self.assertContains(response, f"User1 Cave {i}")
            self.assertNotContains(response, f"User2 Cave {i}")

    def test_user_profile_page_title(self):
        """Test the user profile page title"""
        self.client.force_login(self.user)
        self.user.profile.page_title = "Test Page Title 123"
        self.user.profile.save()

        response = self.client.get(reverse("log:user", args=[self.user.username]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Page Title 123")

    def test_user_profile_page_bio(self):
        """Test the user profile page bio"""
        self.client.force_login(self.user)
        self.user.profile.bio = "Test bio 123"
        self.user.profile.save()

        response = self.client.get(reverse("log:user", args=[self.user.username]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test bio 123")

    def test_private_trips_do_not_appear_on_profile_page_trip_list(self):
        """Test that private trips do not appear on the user profile page"""
        for trip in self.user.trips:
            trip.privacy = Trip.PRIVATE
            trip.save()

        self.client.force_login(self.user2)
        response = self.client.get(reverse("log:user", args=[self.user.username]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "User1 Cave")

    def test_friend_only_trips_do_not_appear_on_profile_page_trip_list(self):
        """Test that friend only trips do not appear on the user profile page"""
        for trip in self.user.trips:
            trip.privacy = Trip.FRIENDS
            trip.save()

        self.client.force_login(self.user2)
        response = self.client.get(reverse("log:user", args=[self.user.username]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "User1 Cave")

    def test_that_friend_only_trips_appear_to_friends(self):
        """Test that friend only trips appear on the user profile page to friends"""
        for trip in self.user.trips:
            trip.privacy = Trip.FRIENDS
            trip.save()

        self.user.profile.friends.add(self.user2)
        self.user2.profile.friends.add(self.user)

        self.client.force_login(self.user2)
        response = self.client.get(reverse("log:user", args=[self.user.username]))
        self.assertEqual(response.status_code, 200)

        for trip in self.user.trips.order_by("-start")[:50]:
            self.assertContains(response, trip.cave_name)

    def test_trip_detail_page_with_various_privacy_settings(self):
        """Test the trip detail page with various privacy settings"""
        trip = self.user.trips.first()
        trip.privacy = Trip.PUBLIC
        trip.save()

        self.client.force_login(self.user2)
        response = self.client.get(reverse("log:trip_detail", args=[trip.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, trip.cave_name)

        trip.privacy = Trip.FRIENDS
        trip.save()
        response = self.client.get(reverse("log:trip_detail", args=[trip.pk]))
        self.assertEqual(response.status_code, 404)

        self.user.profile.friends.add(self.user2)
        self.user2.profile.friends.add(self.user)
        response = self.client.get(reverse("log:trip_detail", args=[trip.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, trip.cave_name)

        trip.privacy = Trip.PRIVATE
        trip.save()
        response = self.client.get(reverse("log:trip_detail", args=[trip.pk]))
        self.assertEqual(response.status_code, 404)

        trip.privacy = Trip.DEFAULT
        trip.save()
        self.user.settings.privacy = UserSettings.PRIVATE
        self.user.settings.save()
        response = self.client.get(reverse("log:trip_detail", args=[trip.pk]))
        self.assertEqual(response.status_code, 404)

        self.user.settings.privacy = UserSettings.PUBLIC
        self.user.settings.save()
        response = self.client.get(reverse("log:trip_detail", args=[trip.pk]))
        self.assertEqual(response.status_code, 200)

        self.user.settings.privacy = UserSettings.FRIENDS
        self.user.settings.save()
        response = self.client.get(reverse("log:trip_detail", args=[trip.pk]))
        self.assertContains(response, trip.cave_name)

        self.user.settings.privacy = UserSettings.PUBLIC
        self.user.settings.save()
        response = self.client.get(reverse("log:trip_detail", args=[trip.pk]))
        self.assertContains(response, trip.cave_name)

        self.client.logout()
        response = self.client.get(reverse("log:trip_detail", args=[trip.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, trip.cave_name)

        self.user.settings.privacy = UserSettings.FRIENDS
        self.user.settings.save()
        response = self.client.get(reverse("log:trip_detail", args=[trip.pk]))
        self.assertEqual(response.status_code, 404)

        self.user.settings.privacy = UserSettings.PRIVATE
        self.user.settings.save()
        response = self.client.get(reverse("log:trip_detail", args=[trip.pk]))
        self.assertEqual(response.status_code, 404)

    def test_user_profile_page_with_various_privacy_settings(self):
        """Test the user profile page with various privacy settings"""
        self.client.force_login(self.user2)
        response = self.client.get(reverse("log:user", args=[self.user.username]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.username)

        self.user.settings.privacy = UserSettings.PRIVATE
        self.user.settings.save()
        response = self.client.get(reverse("log:user", args=[self.user.username]))
        self.assertEqual(response.status_code, 404)

        self.user.settings.privacy = UserSettings.FRIENDS
        self.user.settings.save()
        response = self.client.get(reverse("log:user", args=[self.user.username]))
        self.assertEqual(response.status_code, 404)

        self.user.profile.friends.add(self.user2)
        self.user2.profile.friends.add(self.user)
        response = self.client.get(reverse("log:user", args=[self.user.username]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.username)

        self.user.settings.privacy = UserSettings.PUBLIC
        self.user.settings.save()
        response = self.client.get(reverse("log:user", args=[self.user.username]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.username)

        self.client.logout()
        self.user.settings.privacy = UserSettings.PRIVATE
        self.user.settings.save()
        response = self.client.get(reverse("log:user", args=[self.user.username]))
        self.assertEqual(response.status_code, 404)

        self.user.settings.privacy = UserSettings.FRIENDS
        self.user.settings.save()
        response = self.client.get(reverse("log:user", args=[self.user.username]))
        self.assertEqual(response.status_code, 404)

        self.user.settings.privacy = UserSettings.PUBLIC
        self.user.settings.save()
        response = self.client.get(reverse("log:user", args=[self.user.username]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.username)

    def test_sidebar_displays_properly_when_viewing_another_users_trip(self):
        """Test that the sidebar displays properly when viewing another user's trip"""
        self.client.force_login(self.user2)
        trip = Trip.objects.filter(user=self.user).first()
        response = self.client.get(reverse("log:trip_detail", args=[trip.pk]))
        self.assertContains(response, trip.cave_name)
        self.assertContains(response, f"Trip by {self.user.name}")
        self.assertContains(response, "View profile")
        self.assertContains(response, "View this trip")
        self.assertContains(response, "Add as friend")

        self.assertNotContains(response, reverse("log:trip_update", args=[trip.pk]))
        self.assertNotContains(response, reverse("log:trip_delete", args=[trip.pk]))
        self.assertNotContains(response, reverse("log:report_create", args=[trip.pk]))

    def test_add_as_friend_link_does_not_appear_when_disabled(self):
        """Test that the add as friend link does not appear when disabled"""
        self.user.settings.allow_friend_username = False
        self.user.settings.save()

        self.client.force_login(self.user2)
        trip = Trip.objects.filter(user=self.user).first()
        response = self.client.get(reverse("log:trip_detail", args=[trip.pk]))
        self.assertNotContains(response, "Add as friend")
        self.assertNotContains(response, reverse("users:friend_add"))

    def test_add_as_friend_link_does_not_appear_when_already_friends(self):
        """Test that the add as friend link does not appear when already friends"""
        self.user.profile.friends.add(self.user2)
        self.user2.profile.friends.add(self.user)

        self.client.force_login(self.user2)
        trip = Trip.objects.filter(user=self.user).first()
        response = self.client.get(reverse("log:trip_detail", args=[trip.pk]))
        self.assertNotContains(response, "Add as friend")
        self.assertNotContains(response, reverse("users:friend_add"))

    def test_comments_appear_on_trip_detail_page(self):
        """Test that comments appear on the trip detail page"""
        trip = Trip.objects.filter(user=self.user).first()
        comment = Comment.objects.create(
            author=self.user,
            content_object=trip,
            content="Test comment",
        )
        response = self.client.get(reverse("log:trip_detail", args=[trip.pk]))
        self.assertContains(response, comment.content)

    def test_comments_do_not_appear_on_trip_detail_page_when_disabled(self):
        """Test that comments do not appear on the trip detail page when disabled"""
        self.user.settings.allow_comments = False
        self.user.settings.save()

        trip = Trip.objects.filter(user=self.user).first()
        comment = Comment.objects.create(
            author=self.user2,
            content_object=trip,
            content="Test comment",
        )
        response = self.client.get(reverse("log:trip_detail", args=[trip.pk]))
        self.assertNotContains(response, comment.content)

    def test_comments_appear_on_trip_report_page(self):
        """Test that comments appear on the trip report page"""
        report = TripReport.objects.create(
            user=self.user,
            trip=Trip.objects.filter(user=self.user).first(),
            title="Test report",
            content="Test report content",
            pub_date=tz.now().date(),
        )
        comment = Comment.objects.create(
            author=self.user,
            content_object=report,
            content="Test comment",
        )
        response = self.client.get(reverse("log:report_detail", args=[report.pk]))
        self.assertContains(response, comment.content)

    def test_comments_do_not_appear_on_trip_report_page_when_disabled(self):
        """Test that comments do not appear on the trip report page when disabled"""
        self.user.settings.allow_comments = False
        self.user.settings.save()

        report = TripReport.objects.create(
            user=self.user,
            trip=Trip.objects.filter(user=self.user).first(),
            title="Test report",
            content="Test report content",
            pub_date=tz.now().date(),
        )
        comment = Comment.objects.create(
            author=self.user,
            content_object=report,
            content="Test comment",
        )
        response = self.client.get(reverse("log:report_detail", args=[report.pk]))
        self.assertNotContains(response, comment.content)

    def test_user_profile_is_linked_on_comments(self):
        """Test that the user profile is linked on comments"""
        trip = Trip.objects.filter(user=self.user).first()
        comment = Comment.objects.create(
            author=self.user,
            content_object=trip,
            content="Test comment",
        )
        response = self.client.get(reverse("log:trip_detail", args=[trip.pk]))
        self.assertContains(response, self.user.name)
        self.assertContains(response, comment.content)
        self.assertContains(response, reverse("log:user", args=[self.user.username]))

    def test_user_profile_is_not_linked_on_comments_when_private(self):
        """Test that the user profile is not linked on comments when private"""
        self.user.settings.privacy = UserSettings.PRIVATE
        self.user.settings.save()

        trip = Trip.objects.filter(user=self.user).first()
        trip.privacy = Trip.PUBLIC
        trip.save()

        comment = Comment.objects.create(
            author=self.user,
            content_object=trip,
            content="Test comment",
        )
        response = self.client.get(reverse("log:trip_detail", args=[trip.pk]))
        self.assertContains(response, self.user.name)
        self.assertContains(response, comment.content)
        self.assertNotContains(response, reverse("log:user", args=[self.user.username]))

    def test_trip_report_link_appears_in_sidebar_for_other_users(self):
        """Test that the trip report link appears in the sidebar for other users"""
        trip = Trip.objects.filter(user=self.user).first()
        report = TripReport.objects.create(
            user=self.user,
            trip=trip,
            title="Test report",
            content="Test report content",
            pub_date=tz.now().date(),
        )
        response = self.client.get(reverse("log:trip_detail", args=[trip.pk]))
        self.assertContains(response, reverse("log:report_detail", args=[report.pk]))

    def test_trip_report_link_does_not_appear_in_sidebar_when_private(self):
        """Test that the trip report link does not appear in the sidebar when private"""
        trip = Trip.objects.filter(user=self.user).first()

        report = TripReport.objects.create(
            user=self.user,
            trip=trip,
            title="Test report",
            content="Test report content",
            pub_date=tz.now().date(),
            privacy=TripReport.PRIVATE,
        )
        response = self.client.get(reverse("log:trip_detail", args=[trip.pk]))
        self.assertNotContains(response, reverse("log:report_detail", args=[report.pk]))

    def test_add_comment_via_post_request(self):
        """Test that a comment can be added via a POST request"""
        trip = Trip.objects.filter(user=self.user).first()
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("log:comment_add"),
            {
                "content": "Test comment",
                "type": "trip",
                "pk": trip.pk,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.count(), 1)
        self.assertContains(response, "Test comment")

    def test_add_comment_via_post_request_to_object_the_user_cannot_view(self):
        """Test that a comment cannot be added to an object the user cannot view"""
        trip = Trip.objects.filter(user=self.user).first()
        self.client.force_login(self.user2)

        trip.privacy = Trip.PRIVATE
        trip.save()

        self.client.post(
            reverse("log:comment_add"),
            {
                "content": "Test comment",
                "type": "trip",
                "pk": trip.pk,
            },
        )
        self.assertEqual(Comment.objects.count(), 0)

    def test_add_comment_via_post_request_when_not_logged_in(self):
        """Test that the comment view does not load when not logged in"""
        trip = Trip.objects.filter(user=self.user).first()
        self.client.post(
            reverse("log:comment_add"),
            {
                "content": "Test comment",
                "type": "trip",
                "pk": trip.pk,
            },
        )
        self.assertEqual(Comment.objects.count(), 0)

    def test_delete_comment(self):
        """Test that a comment can be deleted"""
        trip = Trip.objects.filter(user=self.user).first()
        comment = Comment.objects.create(
            author=self.user,
            content_object=trip,
            content="Test comment",
        )
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("log:comment_delete", args=[comment.pk]),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The comment has been deleted")
        self.assertEqual(Comment.objects.count(), 0)

    def test_delete_comment_that_does_not_belong_to_the_user(self):
        """Test that a comment cannot be deleted if it does not belong to the user"""
        trip = Trip.objects.filter(user=self.user2).first()
        comment = Comment.objects.create(
            author=self.user2,
            content_object=trip,
            content="Test comment",
        )
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("log:comment_delete", args=[comment.pk]),
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Comment.objects.count(), 1)

    def test_htmx_like_view_on_an_object_the_user_cannot_view(self):
        """Test that the HTMX like view respects privacy"""
        trip = Trip.objects.filter(user=self.user).first()
        self.client.force_login(self.user2)

        trip.privacy = Trip.PRIVATE
        trip.save()

        response = self.client.get(
            reverse("log:trip_like", args=[trip.pk]),
        )
        self.assertEqual(response.status_code, 404)

    def test_htmx_comment_view_on_an_object_the_user_cannot_view(self):
        """Test that the HTMX comment view respects privacy"""
        trip = Trip.objects.filter(user=self.user).first()
        self.client.force_login(self.user2)

        trip.privacy = Trip.PRIVATE
        trip.save()

        response = self.client.get(
            reverse("log:htmx_trip_comment", args=[trip.pk]),
        )
        self.assertEqual(response.status_code, 404)

    def test_comments_send_a_notification_when_posted(self):
        """Test that a notification is sent when a comment is posted"""
        trip = Trip.objects.filter(user=self.user).first()
        self.client.force_login(self.user2)

        response = self.client.post(
            reverse("log:comment_add"),
            {
                "content": "Test comment",
                "type": "trip",
                "pk": trip.pk,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

        self.client.force_login(self.user)
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(Notification.objects.first().user, self.user)
        self.assertEqual(Notification.objects.first().url, trip.get_absolute_url())

        response = self.client.get(reverse("log:index"))
        self.assertContains(response, f"{self.user2} commented on your trip")

    def test_notification_redirect_view_as_invalid_user(self):
        """Test that the notification redirect view returns a 403 for an invalid user"""
        self.client.force_login(self.user2)
        notification = self.user.notify("Test notification", "/")
        response = self.client.get(
            reverse("users:notification", args=[notification.pk]),
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(notification.read, False)
        self.assertEqual(response.url, reverse("log:index"))

    def test_adding_comment_to_trip_report(self):
        """Test that a comment can be added to a trip report"""
        trip = Trip.objects.filter(user=self.user).first()
        report = TripReport.objects.create(
            user=self.user,
            trip=trip,
            title="Test report",
            content="Test report content",
            pub_date=tz.now().date(),
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("log:comment_add"),
            {
                "content": "Test comment",
                "type": "tripreport",
                "pk": report.pk,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.count(), 1)
        self.assertContains(response, "Test comment")

    def test_adding_comment_to_invalid_object_type(self):
        """Test that a comment cannot be added to an invalid object type"""
        trip = Trip.objects.filter(user=self.user).first()
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("log:comment_add"),
            {
                "content": "Test comment",
                "type": "invalid",
                "pk": trip.pk,
            },
        )
        self.assertEqual(Comment.objects.count(), 0)
        self.assertEqual(response.url, reverse("log:index"))

    def test_adding_comment_with_no_content(self):
        """Test that a comment cannot be added with no content"""
        trip = Trip.objects.filter(user=self.user).first()
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("log:comment_add"),
            {
                "content": "",
                "type": "trip",
                "pk": trip.pk,
            },
            follow=True,
        )
        self.assertContains(response, "This field is required.")
        self.assertEqual(Comment.objects.count(), 0)

    def test_adding_comment_with_too_much_content(self):
        """Test that a comment cannot be added with too much content"""
        trip = Trip.objects.filter(user=self.user).first()
        self.client.force_login(self.user)

        self.client.post(
            reverse("log:comment_add"),
            {
                "content": "x" * 4000,
                "type": "trip",
                "pk": trip.pk,
            },
        )
        self.assertEqual(Comment.objects.count(), 0)

    def test_adding_comment_on_an_object_that_does_not_exist(self):
        """Test that a comment cannot be added to an object that does not exist"""
        self.client.force_login(self.user)

        self.client.post(
            reverse("log:comment_add"),
            {
                "content": "Test comment",
                "type": "trip",
                "pk": 999999999999,
            },
        )
        self.assertEqual(Comment.objects.count(), 0)

    def test_adding_comment_on_an_object_where_the_user_disallows_comments(self):
        """Test users cannot comment where the user disallows comments"""
        self.user.settings.allow_comments = False
        self.user.settings.save()
        trip = Trip.objects.filter(user=self.user).first()
        self.client.force_login(self.user2)

        self.client.post(
            reverse("log:comment_add"),
            {
                "content": "Test comment",
                "type": "trip",
                "pk": trip.pk,
            },
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), 0)

    def test_trip_report_detail_page_with_various_privacy_settings(self):
        """Test that the trip report detail page respects privacy settings"""
        trip = Trip.objects.filter(user=self.user).first()
        report = TripReport.objects.create(
            user=self.user,
            trip=trip,
            title="Test report",
            content="Test report content",
            pub_date=tz.now().date(),
        )
        self.client.force_login(self.user2)

        report.privacy = TripReport.PRIVATE
        report.save()
        response = self.client.get(
            reverse("log:report_detail", args=[report.pk]),
        )
        self.assertEqual(response.status_code, 404)

        report.privacy = TripReport.FRIENDS
        report.save()
        response = self.client.get(
            reverse("log:report_detail", args=[report.pk]),
        )
        self.assertEqual(response.status_code, 404)

        self.user.profile.friends.add(self.user2)
        self.user2.profile.friends.add(self.user)
        response = self.client.get(
            reverse("log:report_detail", args=[report.pk]),
        )
        self.assertEqual(response.status_code, 200)

        report.privacy = TripReport.PUBLIC
        report.save()
        response = self.client.get(
            reverse("log:report_detail", args=[report.pk]),
        )
        self.assertEqual(response.status_code, 200)

        report.privacy = TripReport.DEFAULT
        report.save()
        trip.privacy = Trip.FRIENDS
        trip.save()
        response = self.client.get(
            reverse("log:report_detail", args=[report.pk]),
        )
        self.assertEqual(response.status_code, 200)

        trip.privacy = Trip.PRIVATE
        trip.save()
        response = self.client.get(
            reverse("log:report_detail", args=[report.pk]),
        )
        self.assertEqual(response.status_code, 404)

        trip.privacy = Trip.PUBLIC
        trip.save()
        response = self.client.get(
            reverse("log:report_detail", args=[report.pk]),
        )
        self.assertEqual(response.status_code, 200)


@tag("unit", "fast", "logger")
class TemplateTagUnitTests(TestCase):
    def test_format_metric_templatetag_with_small_value(self):
        """Test the format_metric() function with a small value"""
        self.assertEqual(distformat.format_metric(D(ft=1000)), "305m")

    def test_format_metric_templatetag_with_large_value(self):
        """Test the format_metric() function with a large value"""
        self.assertEqual(distformat.format_metric(D(mi=100)), "160.93km")

    def test_format_imperial_templatetag_with_small_value(self):
        """Test the format_imperial() function with a small value"""
        self.assertEqual(distformat.format_imperial(D(m=100)), "328ft")

    def test_format_imperial_templatetag_with_large_value(self):
        """Test the format_imperial() function with a large value"""
        self.assertEqual(distformat.format_imperial(D(km=100)), "62.14mi")

    def test_distformat_templatetag_with_metric_value(self):
        """Test the distformat() function with a metric value"""
        metric = UserSettings.METRIC
        self.assertEqual(distformat.distformat(D(ft=1000), format=metric), "305m")

    def test_distformat_templatetag_with_imperial_value(self):
        """Test the distformat() function with an imperial value"""
        imperial = UserSettings.IMPERIAL
        self.assertEqual(distformat.distformat(D(km=100), format=imperial), "62.14mi")


class AdminToolsIntegrationTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@admin.app",
            username="admin",
            password="admin",
            name="admin",
        )
        self.admin.is_active = True
        self.admin.is_superuser = True
        self.admin.save()

        self.user = User.objects.create_user(
            email="user@user.app",
            username="user",
            password="user",
            name="user",
        )
        self.user.is_active = True
        self.user.save()

        self.client = Client()

    def test_admin_tools_login_as_form(self):
        """Test the login as form"""
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("log:admin_tools"),
            {
                "login_as": self.user.email,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        user = auth.get_user(self.client)
        self.assertEqual(user, self.user)
        self.assertContains(response, f"Now logged in as {self.user.email}")

    def test_admin_tools_login_as_form_with_a_superuser_account(self):
        """Test the login as form with a superuser account"""
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("log:admin_tools"),
            {
                "login_as": self.admin.email,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cannot login as a superuser via this page")

    def test_admin_tools_notify_all_users_form(self):
        """Test the notify all users form"""
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("log:admin_tools"),
            {
                "notify": "notify",
                "message": "Test message",
                "url": "https://caves.app/",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Notifications sent.")

        self.assertEqual(Notification.objects.count(), 2)
        for notification in Notification.objects.all():
            self.assertEqual(notification.message, "Test message")
            self.assertEqual(notification.url, "https://caves.app/")
