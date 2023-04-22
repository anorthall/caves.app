import logging

from django.contrib.auth import get_user_model
from django.contrib.gis.measure import D
from django.db.utils import IntegrityError
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import datetime as dt
from django.utils.timezone import localtime as lt
from logger import services, statistics

from .models import Trip, TripReport

User = get_user_model()


class TripTestCase(TestCase):
    def setUp(self):
        """Reduce log level to avoid 404 error"""
        logger = logging.getLogger("django.request")
        self.previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)

        # Test user to enable trip creation
        user = User.objects.create_user(
            email="test@test.com",
            username="testusername",
            password="password",
            name="Firstname",
        )
        user.settings.privacy = user.settings.PRIVATE
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
            start=dt.fromisoformat("2010-01-01T13:00:00+00:00"),
        )

        # Create several trips with different privacy settings
        Trip.objects.create(  # Private
            user=user,
            cave_name="Test Cave 3",
            start=dt.fromisoformat("2010-01-01T14:00:00+00:00"),
            privacy=Trip.PRIVATE,
        )
        Trip.objects.create(  # Public
            user=user,
            cave_name="Test Cave 4",
            start=dt.fromisoformat("2010-01-01T15:00:00+00:00"),
            privacy=Trip.PUBLIC,
        )
        Trip.objects.create(  # Default
            user=user,
            cave_name="Test Cave 5",
            start=dt.fromisoformat("2010-01-01T16:00:00+00:00"),
            privacy=Trip.DEFAULT,
        )

        # With distances
        Trip.objects.create(
            user=user,
            cave_name="Test Cave 6",
            start=dt.fromisoformat("2010-01-01T17:00:00+00:00"),
            end=dt.fromisoformat("2010-01-01T19:00:00+00:00"),
            vert_dist_down="100m",
            vert_dist_up="200m",
            horizontal_dist="300m",
            surveyed_dist="400m",
            resurveyed_dist="500m",
            aid_dist="600m",
        )

    def tearDown(self):
        """Reset the log level back to normal"""
        logger = logging.getLogger("django.request")
        logger.setLevel(self.previous_level)

    def test_trip_duration_and_duration_str(self):
        """
        Check that trip duration returns a timedelta with the correct value
        Check that trip duration returns None if no end time
        Check that trip duration_str returns a string with the correct value
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

        trip = Trip.objects.get(cave_name="Test Cave 1")
        trip.end = dt.fromisoformat("2010-01-02T13:01:00+00:00")
        trip.save()
        self.assertEqual(trip.duration_str, "1 day, 1 hour and 1 minute")

        trip = Trip.objects.get(cave_name="Test Cave 1")
        trip.end = dt.fromisoformat("2010-01-03T14:02:00+00:00")
        trip.save()
        self.assertEqual(trip.duration_str, "2 days, 2 hours and 2 minutes")

    def test_has_distances_property(self):
        """Test the Trip.has_distances property"""
        trip = Trip.objects.get(cave_name="Test Cave 6")
        self.assertTrue(trip.has_distances)

        trip = Trip.objects.get(cave_name="Test Cave 1")
        self.assertFalse(trip.has_distances)

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

    def test_trip_number_property(self):
        """Test the Trip.number property"""
        qs = Trip.objects.all()
        x = 1
        for trip in qs:
            self.assertEqual(trip.number, x)
            x += 1

    def test_trip_index(self):
        """Test the Trip.trip_index class method"""
        user = User.objects.get(username="testusername")
        trip_index = services.trip_index(user)
        self.assertEqual(len(trip_index), 6)
        for trip in Trip.objects.all():
            self.assertEqual(trip_index[trip.pk], trip.number)

    def test_stats_for_user(self):
        """Test the stats_for_user method from the statistics module"""
        user = User.objects.get(username="testusername")
        self.assertEqual(user.trips.count(), 6)
        stats = statistics.stats_for_user(user.trips)
        self.assertEqual(stats["trips"], 6)
        self.assertEqual(stats["vert_down"], D(m=100))
        self.assertEqual(stats["vert_up"], D(m=200))
        self.assertEqual(stats["horizontal"], D(m=300))
        self.assertEqual(stats["surveyed"], D(m=400))
        self.assertEqual(stats["resurveyed"], D(m=500))
        self.assertEqual(stats["aided"], D(m=600))
        self.assertEqual(stats["time"], "4 hours")

    def test_surface_trips_are_not_counted_towards_stats(self):
        """Test that surface trips are not counted towards stats"""
        user = User.objects.get(username="testusername")
        Trip.objects.create(
            user=user,
            cave_name="Surface Trip",
            start=dt.fromisoformat("2010-01-01T12:00:00+00:00"),
            end=dt.fromisoformat("2010-01-01T14:00:00+00:00"),
            vert_dist_down="100m",
            vert_dist_up="200m",
            horizontal_dist="300m",
            surveyed_dist="400m",
            resurveyed_dist="500m",
            aid_dist="600m",
            type=Trip.SURFACE,
        )
        stats = statistics.stats_for_user(user.trips)
        self.assertEqual(stats["trips"], 6)
        self.assertEqual(stats["vert_down"], D(m=100))
        self.assertEqual(stats["vert_up"], D(m=200))
        self.assertEqual(stats["horizontal"], D(m=300))
        self.assertEqual(stats["surveyed"], D(m=400))
        self.assertEqual(stats["resurveyed"], D(m=500))
        self.assertEqual(stats["aided"], D(m=600))
        self.assertEqual(stats["time"], "4 hours")

    def test_stats_for_user_with_no_trips(self):
        """Test the Trip.stats_for_user class method with no trips"""
        user = User.objects.create_user(
            email="test_no_trips@test.com",
            username="testusername2",
            password="testpassword",
            name="Joe",
        )
        stats = statistics.stats_for_user(user.trips)
        self.assertEqual(stats["trips"], 0)
        self.assertEqual(stats["vert_down"], D(m=0))
        self.assertEqual(stats["vert_up"], D(m=0))
        self.assertEqual(stats["horizontal"], D(m=0))
        self.assertEqual(stats["surveyed"], D(m=0))
        self.assertEqual(stats["resurveyed"], D(m=0))
        self.assertEqual(stats["aided"], D(m=0))
        self.assertEqual(stats["time"], "0")

    def test_next_and_prev_trip_properties(self):
        """Test the Trip.next_trip and Trip.prev_trip properties"""
        trip = Trip.objects.get(cave_name="Test Cave 1")
        self.assertEqual(trip.prev_trip, None)
        self.assertEqual(trip.next_trip.cave_name, "Test Cave 2")
        self.assertEqual(trip.next_trip.number, trip.number + 1)

        trip = Trip.objects.get(cave_name="Test Cave 6")
        self.assertEqual(trip.next_trip, None)
        self.assertEqual(trip.prev_trip.cave_name, "Test Cave 5")
        self.assertEqual(trip.prev_trip.number, trip.number - 1)


class TripIntegrationTests(TestCase):
    def setUp(self):
        """Reduce log level to avoid 404 error"""
        logger = logging.getLogger("django.request")
        self.previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)

        self.client = Client()

        # Create a user
        self.superuser = User.objects.create_superuser(
            email="super@user.app",
            username="superuser",
            password="testpassword",
            name="Joe",
        )
        self.superuser.is_active = True
        self.superuser.save()

        # Create an enabled user
        self.enabled = User.objects.create_user(
            email="enabled@user.app",
            username="enabled",
            password="testpassword",
            name="Joe",
        )
        self.enabled.is_active = True
        self.enabled.save()

        # Create a disabled user
        self.disabled = User.objects.create_user(
            email="disabled@user.app",
            username="disabled",
            password="testpassword",
            name="Joe",
        )
        self.disabled.is_active = False
        self.disabled.save()

        # Create a trip belonging to the superuser
        self.trip = Trip.objects.create(
            user=self.superuser,
            cave_name="Test Cave",
            start=timezone.now() - timezone.timedelta(days=1),
            end=timezone.now(),
        )

    def tearDown(self):
        """Reset the log level back to normal"""
        logger = logging.getLogger("django.request")
        logger.setLevel(self.previous_level)

    def test_non_superuser_cannot_access_admin_tools(self):
        """Test that a non-superuser cannot access the admin tools"""
        self.client.login(email="enabled@user.app", password="testpassword")
        response = self.client.get("/admin-tools/")
        self.assertEqual(response.status_code, 404)

    def test_anonymous_user_cannot_access_trip_pages(self):
        """Test that an anonymous user cannot access trip pages"""
        pages = [
            f"/trip/{self.trip.pk}/",
            f"/trip/edit/{self.trip.pk}/",
            f"/trip/delete/{self.trip.pk}/",
            "/trip/add/",
            "/trips/",
            "/trips/export/",
        ]
        for page in pages:
            response = self.client.get(page)
            self.assertIn(response.status_code, [301, 302])
            self.assertEqual(response.url, "/account/login/?next=" + page)

    def test_about_page(self):
        """Test the about page"""
        response = self.client.get("/about/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "<strong>" + str(Trip.objects.all().count()) + "</strong>"
        )
        self.assertContains(
            response,
            "<strong>" + str(User.objects.all().count()) + "</strong>",
        )

    def test_csv_export(self):
        """Test the CSV export"""
        user = self.enabled
        self.client.login(email="enabled@user.app", password="testpassword")

        # Add 100 trips with random data to the user
        from random import random

        trips = []
        for i in range(100):
            trips.append(
                Trip(
                    user=self.enabled,
                    cave_name="Test Cave " + str(i),
                    cave_region=str(random()),
                    cave_country=str(random()),
                    cavers=str(random()),
                    start=timezone.now() - timezone.timedelta(days=1),
                    end=timezone.now(),
                )
            )
        Trip.objects.bulk_create(trips)

        # Get the CSV export
        response = self.client.post("/trips/export/", {"download": "download"})
        timestamp = timezone.now().strftime("%Y-%m-%d-%H%M")
        filename = f"{user.username}-trips-{timestamp}.csv"
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertEqual(
            response["Content-Disposition"], f'attachment; filename="{filename}"'
        )

        # Check the CSV file
        import csv
        import io

        csv_data = response.content.decode("utf-8")
        reader = csv.reader(io.StringIO(csv_data))

        i = 0
        next(reader)  # Skip the header row
        for trip in trips:
            row = next(reader)
            self.assertEqual(row[1], trip.cave_name)
            self.assertEqual(row[2], trip.cave_region)
            self.assertEqual(row[3], trip.cave_country)
            self.assertEqual(row[9], trip.cavers)
            self.assertEqual(row[5], lt(trip.start).strftime("%Y-%m-%d %H:%M"))
            self.assertEqual(row[6], lt(trip.end).strftime("%Y-%m-%d %H:%M"))
            i += 1

    def test_trip_list_view(self):
        """Test the trip list view"""
        self.client.login(email="enabled@user.app", password="testpassword")

        # Create 50 trips with randomised names
        from random import random

        trips = []
        for i in range(50):
            trips.append(
                Trip(
                    user=self.enabled,
                    cave_name="Test Cave " + str(random()),
                    start=timezone.now(),
                )
            )
        Trip.objects.bulk_create(trips)

        # Get the trip list page
        response = self.client.get(f"/u/enabled/")
        self.assertEqual(response.status_code, 200)
        for trip in trips:
            self.assertContains(response, trip.cave_name)

    def test_trip_list_page_only_lists_users_trips(self):
        """Test that the trip list page only lists the users trips"""
        self.client.login(email="enabled@user.app", password="testpassword")
        # Create 10 trips for another user
        from random import random

        other_trips = []
        for i in range(10):
            other_trips.append(
                Trip(
                    user=self.superuser,
                    cave_name="Other User Trip " + str(random()),
                    start=timezone.now(),
                )
            )
        Trip.objects.bulk_create(other_trips)

        # Create 10 trips for the active user
        trips = []
        for i in range(10):
            trips.append(
                Trip(
                    user=self.enabled,
                    cave_name="Test Cave " + str(random()),
                    start=timezone.now(),
                )
            )
        Trip.objects.bulk_create(trips)

        # Get the trip list page
        response = self.client.get(reverse("log:user", args=[self.enabled.username]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Other User Trip")

        for trip in trips:
            self.assertContains(response, trip.cave_name)

        for trip in other_trips:
            self.assertNotContains(response, trip.cave_name)

    def test_trip_creation_form(self):
        """Test the trip creation form"""
        self.client.login(email="enabled@user.app", password="testpassword")
        response = self.client.get("/trip/add/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Add a trip")
        self.assertContains(response, "Cave name")
        self.assertContains(response, "Cave region")
        self.assertContains(response, "Cave country")
        self.assertContains(response, "Cavers")
        self.assertContains(response, "Notes")
        self.assertContains(response, "Save")

        response = self.client.post(
            "/trip/add/",
            {
                "cave_name": "Test The Form Cave",
                "cave_region": "Test Region",
                "cave_country": "Test Country",
                "type": Trip.SPORT,
                "cavers": "Test Cavers",
                "start": timezone.now(),
                "end": timezone.now() + timezone.timedelta(days=1),
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

    def test_trip_update_form(self):
        """Test the trip update form"""
        self.client.login(email="super@user.app", password="testpassword")
        response = self.client.get(f"/trip/edit/{self.trip.pk}/")
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
            f"/trip/edit/{self.trip.pk}/",
            {
                "cave_name": "Test The Form Cave",
                "cave_region": "Test Region",
                "cave_country": "Test Country",
                "type": Trip.SPORT,
                "cavers": "Test Cavers",
                "start": timezone.now(),
                "end": timezone.now() + timezone.timedelta(days=1),
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


class TripReportTestCase(TestCase):
    def setUp(self):
        """Reduce log level to avoid 404 error"""
        logger = logging.getLogger("django.request")
        self.previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)

        self.user = User.objects.create_user(
            email="test@user.app",
            username="username",
            password="password",
            name="Test",
        )
        self.user.is_active = True
        self.user.save()

        self.trip = Trip.objects.create(
            user=self.user,
            cave_name="Test Cave",
            start=timezone.now(),
        )

    def tearDown(self):
        """Reset the log level back to normal"""
        logger = logging.getLogger("django.request")
        logger.setLevel(self.previous_level)

    def test_slug_is_unique_for_user_only(self):
        """Test that the slug is unique for the user only"""
        # Create a trip report for the user with slug 'slug'
        TripReport.objects.create(
            user=self.user,
            trip=self.trip,
            title="Test Report",
            slug="slug",
            content="Test Content",
            pub_date=timezone.now().date(),
        )

        # Create another user, trip, and trip report with the same slug
        # This code running without exception is considered a 'pass'.
        user2 = User.objects.create_user(
            email="test2@users.app",
            username="username2",
            password="password2",
            name="Test2",
        )
        trip2 = Trip.objects.create(
            user=user2,
            cave_name="Test Cave 2",
            start=timezone.now(),
        )
        TripReport.objects.create(
            user=user2,
            trip=trip2,
            title="Test Report 2",
            slug="slug",
            content="Test Content 2",
            pub_date=timezone.now().date(),
        )

        # Now create a second trip/report for the original user with the same
        # slug. This should fail with an IntegrityError.
        with self.assertRaises(IntegrityError):
            trip = Trip.objects.create(
                user=self.user,
                cave_name="Test Cave",
                start=timezone.now(),
            )
            TripReport.objects.create(
                user=self.user,
                trip=trip,
                title="Test Report",
                slug="slug",
                content="Test Content",
                pub_date=timezone.now().date(),
            )

    def test_report_privacy(self):
        """Test the TripReport.is_private and TripReport.is_public methods"""
        # Test default privacy when the trip is set to default and the user is private
        self.user.settings.privacy = self.user.settings.PRIVATE
        self.user.settings.save()
        self.trip.privacy = Trip.DEFAULT
        self.trip.save()

        self.assertTrue(self.user.is_private)
        self.assertEqual(self.trip.privacy, Trip.DEFAULT)

        report = TripReport.objects.create(
            user=self.user,
            trip=self.trip,
            title="Test Report",
            slug="slug",
            content="Test Content",
            pub_date=timezone.now().date(),
            privacy=TripReport.DEFAULT,
        )
        self.assertEqual(report.privacy, TripReport.DEFAULT)
        self.assertTrue(report.is_private)
        self.assertFalse(report.is_public)

        # Test default privacy when the trip is set to default and the user is public
        self.user.settings.privacy = self.user.settings.PUBLIC
        self.user.settings.save()

        self.assertEqual(report.privacy, TripReport.DEFAULT)
        self.assertTrue(self.user.is_public)
        self.assertEqual(self.trip.privacy, Trip.DEFAULT)
        self.assertFalse(report.is_private)
        self.assertTrue(report.is_public)

        # Test default privacy when the trip is set to public and the user is private
        self.user.settings.privacy = self.user.settings.PRIVATE
        self.user.settings.save()
        self.trip.privacy = Trip.PUBLIC
        self.trip.save()

        self.assertEqual(report.privacy, TripReport.DEFAULT)
        self.assertTrue(self.user.is_private)
        self.assertTrue(self.trip.is_public)
        self.assertFalse(report.is_private)
        self.assertTrue(report.is_public)

        # Test default privacy when the trip is private and the user is public
        self.user.settings.privacy = self.user.settings.PUBLIC
        self.user.settings.save()
        self.trip.privacy = Trip.PRIVATE
        self.trip.save()

        self.assertEqual(report.privacy, TripReport.DEFAULT)
        self.assertTrue(self.user.is_public)
        self.assertTrue(self.trip.is_private)
        self.assertTrue(report.is_private)
        self.assertFalse(report.is_public)

        # Test public privacy when the trip is set to default and the user is private
        self.user.settings.privacy = self.user.settings.PRIVATE
        self.user.settings.save()
        self.trip.privacy = Trip.DEFAULT
        self.trip.save()
        report.privacy = TripReport.PUBLIC
        report.save()

        self.assertEqual(report.privacy, TripReport.PUBLIC)
        self.assertTrue(self.user.is_private)
        self.assertEqual(self.trip.privacy, Trip.DEFAULT)
        self.assertFalse(report.is_private)
        self.assertTrue(report.is_public)

        # Test public privacy when the trip is set to default and the user is public
        self.user.settings.privacy = self.user.settings.PUBLIC
        self.user.settings.save()
        self.trip.privacy = Trip.DEFAULT
        self.trip.save()

        self.assertEqual(report.privacy, TripReport.PUBLIC)
        self.assertTrue(self.user.is_public)
        self.assertEqual(self.trip.privacy, Trip.DEFAULT)
        self.assertFalse(report.is_private)
        self.assertTrue(report.is_public)

        # Test public privacy when the trip is set to public and the user is private
        self.user.settings.privacy = self.user.settings.PRIVATE
        self.user.settings.save()
        self.trip.privacy = Trip.PUBLIC
        self.trip.save()

        self.assertEqual(report.privacy, TripReport.PUBLIC)
        self.assertTrue(self.user.is_private)
        self.assertTrue(self.trip.is_public)
        self.assertFalse(report.is_private)
        self.assertTrue(report.is_public)

        # Test public privacy when the trip is private and the user is public
        self.user.settings.privacy = self.user.settings.PUBLIC
        self.user.settings.save()
        self.trip.privacy = Trip.PRIVATE
        self.trip.save()

        self.assertEqual(report.privacy, TripReport.PUBLIC)
        self.assertTrue(self.user.is_public)
        self.assertTrue(self.trip.is_private)
        self.assertFalse(report.is_private)
        self.assertTrue(report.is_public)

        # Test public privacy when the trip is private and the user is private
        self.user.settings.privacy = self.user.settings.PRIVATE
        self.user.settings.save()
        self.trip.privacy = Trip.PRIVATE
        self.trip.save()

        self.assertEqual(report.privacy, TripReport.PUBLIC)
        self.assertTrue(self.user.is_private)
        self.assertTrue(self.trip.is_private)
        self.assertFalse(report.is_private)
        self.assertTrue(report.is_public)

        # Test private privacy when the trip is set to default and the user is private
        self.user.settings.privacy = self.user.settings.PRIVATE
        self.user.settings.save()
        self.trip.privacy = Trip.DEFAULT
        self.trip.save()
        report.privacy = TripReport.PRIVATE
        report.save()

        self.assertEqual(report.privacy, TripReport.PRIVATE)
        self.assertTrue(self.user.is_private)
        self.assertEqual(self.trip.privacy, Trip.DEFAULT)
        self.assertTrue(report.is_private)
        self.assertFalse(report.is_public)

        # Test private privacy when the trip is set to default and the user is public
        self.user.settings.privacy = self.user.settings.PUBLIC
        self.user.settings.save()
        self.trip.privacy = Trip.DEFAULT
        self.trip.save()

        self.assertEqual(report.privacy, TripReport.PRIVATE)
        self.assertTrue(self.user.is_public)
        self.assertEqual(self.trip.privacy, Trip.DEFAULT)
        self.assertTrue(report.is_private)
        self.assertFalse(report.is_public)

        # Test private privacy when the trip is set to public and the user is private
        self.user.settings.privacy = self.user.settings.PRIVATE
        self.user.settings.save()
        self.trip.privacy = Trip.PUBLIC
        self.trip.save()

        self.assertEqual(report.privacy, TripReport.PRIVATE)
        self.assertTrue(self.user.is_private)
        self.assertTrue(self.trip.is_public)
        self.assertTrue(report.is_private)
        self.assertFalse(report.is_public)

        # Test private privacy when the trip is private and the user is public
        self.user.settings.privacy = self.user.settings.PUBLIC
        self.user.settings.save()
        self.trip.privacy = Trip.PRIVATE
        self.trip.save()

        self.assertEqual(report.privacy, TripReport.PRIVATE)
        self.assertTrue(self.user.is_public)
        self.assertTrue(self.trip.is_private)
        self.assertTrue(report.is_private)
        self.assertFalse(report.is_public)

        # Test private privacy when the trip is private and the user is private
        self.user.settings.privacy = self.user.settings.PRIVATE
        self.user.settings.save()
        self.trip.privacy = Trip.PRIVATE
        self.trip.save()

        self.assertEqual(report.privacy, TripReport.PRIVATE)
        self.assertTrue(self.user.is_private)
        self.assertTrue(self.trip.is_private)
        self.assertTrue(report.is_private)
        self.assertFalse(report.is_public)

    def test_trip_report_create_view(self):
        """Test the trip report create view in GET and POST."""
        # Test view loads
        self.client.login(email="test@user.app", password="password")
        response = self.client.get(f"/report/add/{self.trip.pk}/")
        self.assertEqual(response.status_code, 200)

        # Test post request
        response = self.client.post(
            f"/report/add/{self.trip.pk}/",
            {
                "title": "Test Report",
                "pub_date": dt.now().date(),
                "slug": "test-report",
                "content": "Test content.",
                "privacy": TripReport.PUBLIC,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"/report/{self.trip.pk}/")
        self.assertEqual(TripReport.objects.count(), 1)
        self.assertEqual(TripReport.objects.get().title, "Test Report")
        self.assertEqual(TripReport.objects.get().content, "Test content.")
        self.assertEqual(TripReport.objects.get().privacy, TripReport.PUBLIC)
        self.assertEqual(TripReport.objects.get().trip, self.trip)

    def test_trip_report_create_view_with_duplicate_slug(self):
        """Test the trip report create view in POST with a duplicate slug."""
        # Create a report with the slug 'slug'
        TripReport.objects.create(
            title="Test Report",
            pub_date=dt.now().date(),
            slug="slug",
            content="Test content.",
            privacy=TripReport.PUBLIC,
            trip=self.trip,
            user=self.user,
        )

        # Create a new trip
        trip = Trip.objects.create(
            cave_name="Test Trip",
            start=timezone.now(),
            user=self.user,
        )

        # Submit a POST request with the same slug
        self.client.login(email="test@user.app", password="password")
        response = self.client.post(
            f"/report/add/{trip.pk}/",
            {
                "title": "Test Report",
                "pub_date": dt.now().date(),
                "slug": "slug",
                "content": "Test content.",
                "privacy": TripReport.PUBLIC,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(TripReport.objects.count(), 1)
        self.assertContains(response, "The slug must be unique.")

        # Create a new user, trip, and report and test the slug is allowed
        user = User.objects.create_user(
            email="new@user.app",
            password="password",
            username="newuser",
            name="New",
        )
        user.is_active = True
        user.save()

        trip = Trip.objects.create(
            cave_name="Test Trip",
            start=timezone.now(),
            user=user,
        )

        # Submit a POST request as the new user with the slug 'slug'
        self.client.login(email="new@user.app", password="password")
        response = self.client.post(
            f"/report/add/{trip.pk}/",
            {
                "title": "Test Report as new user",
                "pub_date": dt.now().date(),
                "slug": "slug",
                "content": "Test content.",
                "privacy": TripReport.PUBLIC,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(TripReport.objects.count(), 2)
        self.assertEqual(TripReport.objects.last().title, "Test Report as new user")

    def test_trip_report_create_view_redirects_if_a_report_already_exists(self):
        """Test the trip report create view redirects if a report already exists for that trip."""
        # Create a report
        report = TripReport.objects.create(
            title="Test Report",
            pub_date=dt.now().date(),
            slug="test-report",
            content="Test content.",
            privacy=TripReport.PUBLIC,
            trip=self.trip,
            user=self.user,
        )

        # Test the view redirects
        self.client.login(email="test@user.app", password="password")
        response = self.client.get(f"/report/add/{self.trip.pk}/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"/report/{report.pk}/")

    def test_users_cannot_edit_a_trip_report_for_other_users(self):
        """Test users cannot edit a trip report which does not belong to them."""
        # Create a new user
        user = User.objects.create_user(
            email="new@user.app",
            password="password",
            username="testuser",
            name="Test",
        )
        user.is_active = True
        user.save()

        # Create a trip report
        report = TripReport.objects.create(
            title="Test Report",
            pub_date=dt.now().date(),
            slug="test-report",
            content="Test content.",
            privacy=TripReport.PUBLIC,
            trip=self.trip,
            user=self.user,
        )

        # Test the user cannot delete edit the report
        self.client.login(email="new@user.app", password="password")
        response = self.client.get(f"/report/edit/{report.pk}/")
        self.assertEqual(response.status_code, 404)

        # Test the user cannot delete the report
        response = self.client.get(f"/report/delete/{report.pk}/")
        self.assertEqual(response.status_code, 404)

        # Test user cannot create a report for a trip belonging to another user
        response = self.client.get(f"/report/add/{self.trip.pk}/")
        self.assertEqual(response.status_code, 404)

    def test_users_can_view_and_edit_their_own_trip_reports(self):
        """Test users can view and edit their own trip reports."""
        # Create a trip report
        report = TripReport.objects.create(
            title="Test Report",
            pub_date=dt.now().date(),
            slug="test-report",
            content="Test content.",
            privacy=TripReport.PUBLIC,
            trip=self.trip,
            user=self.user,
        )

        # Test the user can view the report
        self.client.login(email="test@user.app", password="password")
        response = self.client.get(f"/report/{report.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Report")
        self.assertContains(response, "Test content.")

        # Test the user can edit the report
        response = self.client.get(f"/report/edit/{report.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Report")
        self.assertContains(response, "Test content.")

        # Test the user can POST to the edit view
        response = self.client.post(
            f"/report/edit/{report.pk}/",
            {
                "title": "Test Report Updated",
                "pub_date": dt.now().date(),
                "slug": "test-report-updated",
                "content": "Test content updated.",
                "privacy": TripReport.PUBLIC,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"/report/{report.pk}/")
        report.refresh_from_db()
        self.assertEqual(report.title, "Test Report Updated")
        self.assertEqual(report.slug, "test-report-updated")
        self.assertEqual(report.content, "Test content updated.")

        # Test the user can delete the report
        response = self.client.get(f"/report/delete/{report.pk}/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"/trip/{self.trip.pk}/")
        self.assertEqual(TripReport.objects.count(), 0)

    def test_trip_report_link_appears_on_trip_list(self):
        """Test the trip report link appears on the trip list page."""
        self.client.login(email="test@user.app", password="password")
        # Create a trip report
        report = TripReport.objects.create(
            title="Test Report",
            pub_date=dt.now().date(),
            slug="test-report",
            content="Test content.",
            privacy=TripReport.PUBLIC,
            trip=self.trip,
            user=self.user,
        )

        # Test the link appears on the trip list page
        response = self.client.get(reverse("log:user", args=[self.user.username]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"/report/{report.pk}/")

    def test_trip_report_link_appears_on_trip_detail(self):
        """Test the trip report link appears on the trip detail page."""
        self.client.login(email="test@user.app", password="password")
        # Create a trip report
        report = TripReport.objects.create(
            title="Test Report",
            pub_date=dt.now().date(),
            slug="test-report",
            content="Test content.",
            privacy=TripReport.PUBLIC,
            trip=self.trip,
            user=self.user,
        )

        # Test the link appears on the trip detail page
        response = self.client.get(f"/trip/{self.trip.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"/report/{report.pk}/")

    def test_add_trip_report_appears_when_no_report_added(self):
        """Test the add trip report link appears on the trip detail page when no report has been added."""
        # Test the link appears on the trip detail page
        self.client.login(email="test@user.app", password="password")
        response = self.client.get(f"/trip/{self.trip.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"/report/add/{self.trip.pk}/")

    def test_add_trip_report_does_not_appear_when_report_added(self):
        """Test the add trip report link does not appear on the trip detail page when a report has been added."""
        self.client.login(email="test@user.app", password="password")
        # Create a trip report
        TripReport.objects.create(
            title="Test Report",
            pub_date=dt.now().date(),
            slug="test-report",
            content="Test content.",
            privacy=TripReport.PUBLIC,
            trip=self.trip,
            user=self.user,
        )

        # Test the link does not appear on the trip detail page
        response = self.client.get(f"/trip/{self.trip.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, f"/report/add/{self.trip.pk}/")

    def test_view_and_edit_trip_report_links_appear_when_a_report_has_been_added(self):
        """Test the view and edit trip report links appear on the trip detail page when a report has been added."""
        self.client.login(email="test@user.app", password="password")
        # Create a trip report
        report = TripReport.objects.create(
            title="Test Report",
            pub_date=dt.now().date(),
            slug="test-report",
            content="Test content.",
            privacy=TripReport.PUBLIC,
            trip=self.trip,
            user=self.user,
        )

        # Test the links appear on the trip detail page
        response = self.client.get(f"/trip/{self.trip.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"/report/{report.pk}/")
        self.assertContains(response, f"/report/edit/{report.pk}/")
