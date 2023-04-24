import logging

from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from django.test import Client, TestCase, tag
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import datetime as dt

from .models import Trip, TripReport

User = get_user_model()


@tag("core", "fast", "unit")
class TripModelUnitTests(TestCase):
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
            cave_name="Duration Trip",
            start=dt.fromisoformat("2010-01-01T12:00:00+00:00"),
            end=dt.fromisoformat("2010-01-01T14:00:00+00:00"),
        )

        # Trip with no end time
        Trip.objects.create(
            user=user,
            cave_name="No Duration Trip",
            start=dt.fromisoformat("2010-01-01T13:00:00+00:00"),
        )

        Trip.objects.create(
            user=user,
            cave_name="Private Trip",
            start=dt.fromisoformat("2010-01-01T14:00:00+00:00"),
            privacy=Trip.PRIVATE,
        )
        Trip.objects.create(
            user=user,
            cave_name="Public Trip",
            start=dt.fromisoformat("2010-01-01T15:00:00+00:00"),
            privacy=Trip.PUBLIC,
        )
        Trip.objects.create(
            user=user,
            cave_name="Default Trip",
            start=dt.fromisoformat("2010-01-01T16:00:00+00:00"),
            privacy=Trip.DEFAULT,
        )

        Trip.objects.create(
            user=user,
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
        self.assertEqual(trip_with_end.duration, timezone.timedelta(hours=2))

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


class TripIntegrationTests(TestCase):
    def setUp(self):
        """Reduce log level to avoid 404 error"""
        logger = logging.getLogger("django.request")
        self.previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)

        self.client = Client()

        # Create an enabled user
        self.enabled = User.objects.create_user(
            email="enabled@user.app",
            username="enabled",
            password="testpassword",
            name="Joe",
        )
        self.enabled.is_active = True
        self.enabled.save()

        # Create a trip
        self.trip = Trip.objects.create(
            user=self.enabled,
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
        self.client.force_login(self.enabled)
        response = self.client.get(reverse("log:admin_tools"))
        self.assertEqual(response.status_code, 404)

    def test_trip_list_view(self):
        """Test the trip list view"""
        self.client.force_login(self.enabled)

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

        response = self.client.get(reverse("log:user", args=[self.enabled.username]))
        self.assertEqual(response.status_code, 200)
        for trip in trips:
            self.assertContains(response, trip.cave_name)

    def test_trip_creation_form(self):
        """Test the trip creation form"""
        self.client.force_login(self.enabled)
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
        self.client.force_login(self.enabled)
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
        self.assertEqual(trip.user, self.enabled)


class TripReportIntegrationTests(TestCase):
    def setUp(self):
        """Reduce log level to avoid 404 error"""
        logger = logging.getLogger("django.request")
        self.previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)

        # Create an enabled user
        self.enabled = User.objects.create_user(
            email="enabled@user.app",
            username="enabled",
            password="testpassword",
            name="Joe",
        )
        self.enabled.is_active = True
        self.enabled.save()

        self.trip = Trip.objects.create(
            user=self.enabled,
            cave_name="Test Cave",
            start=timezone.now(),
        )

    def tearDown(self):
        """Reset the log level back to normal"""
        logger = logging.getLogger("django.request")
        logger.setLevel(self.previous_level)

    def test_slug_is_unique_for_user_only(self):
        """Test that the slug is unique for the user only"""
        TripReport.objects.create(
            user=self.enabled,
            trip=self.trip,
            title="Test Report",
            slug="slug",
            content="Test Content",
            pub_date=timezone.now().date(),
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

        # Now create a second trip/report for the original user with the same slug
        with self.assertRaises(IntegrityError):
            trip = Trip.objects.create(
                user=self.enabled,
                cave_name="Test Cave",
                start=timezone.now(),
            )
            TripReport.objects.create(
                user=self.enabled,
                trip=trip,
                title="Test Report",
                slug="slug",
                content="Test Content",
                pub_date=timezone.now().date(),
            )

    def test_trip_report_create_view(self):
        """Test the trip report create view in GET and POST"""
        self.client.force_login(self.enabled)
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

    def test_trip_report_create_view_redirects_if_a_report_already_exists(self):
        """Test the trip report create view redirects if a report already exists"""
        report = TripReport.objects.create(
            title="Test Report",
            pub_date=dt.now().date(),
            slug="test-report",
            content="Test content.",
            privacy=TripReport.PUBLIC,
            trip=self.trip,
            user=self.enabled,
        )

        self.client.force_login(self.enabled)
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
            user=self.enabled,
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
            user=self.enabled,
        )

        self.client.force_login(self.enabled)
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
                "slug": "test-report-updated",
                "content": "Test content updated.",
                "privacy": TripReport.PUBLIC,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("log:report_detail", args=[report.pk]))
        report.refresh_from_db()
        self.assertEqual(report.title, "Test Report Updated")
        self.assertEqual(report.slug, "test-report-updated")
        self.assertEqual(report.content, "Test content updated.")

        response = self.client.get(reverse("log:report_delete", args=[report.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("log:trip_detail", args=[self.trip.pk]))
        self.assertEqual(TripReport.objects.count(), 0)

    def test_trip_report_link_appears_on_trip_list(self):
        """Test the trip report link appears on the trip list page."""
        self.client.force_login(self.enabled)
        report = TripReport.objects.create(
            title="Test Report",
            pub_date=dt.now().date(),
            slug="test-report",
            content="Test content.",
            privacy=TripReport.PUBLIC,
            trip=self.trip,
            user=self.enabled,
        )

        response = self.client.get(reverse("log:user", args=[self.enabled.username]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("log:report_detail", args=[report.pk]))

    def test_trip_report_link_appears_on_trip_detail(self):
        """Test the trip report link appears on the trip detail page"""
        self.client.force_login(self.enabled)
        report = TripReport.objects.create(
            title="Test Report",
            pub_date=dt.now().date(),
            slug="test-report",
            content="Test content.",
            privacy=TripReport.PUBLIC,
            trip=self.trip,
            user=self.enabled,
        )

        response = self.client.get(reverse("log:trip_detail", args=[self.trip.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("log:report_detail", args=[report.pk]))

    def test_add_trip_report_link_appears_when_no_report_has_been_added(self):
        """Test the add trip report link appears on the trip detail page"""
        self.client.force_login(self.enabled)
        response = self.client.get(reverse("log:trip_detail", args=[self.trip.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("log:report_create", args=[self.trip.pk]))

    def test_add_trip_report_does_not_appear_when_report_added(self):
        """Test the add trip report link does not appear on the detail page"""
        self.client.force_login(self.enabled)
        TripReport.objects.create(
            title="Test Report",
            pub_date=dt.now().date(),
            slug="test-report",
            content="Test content.",
            privacy=TripReport.PUBLIC,
            trip=self.trip,
            user=self.enabled,
        )

        response = self.client.get(reverse("log:trip_detail", args=[self.trip.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(
            response, reverse("log:report_create", args=[self.trip.pk])
        )

    def test_view_and_edit_trip_report_links_appear_when_a_report_has_been_added(self):
        """Test the view and edit trip report links appear on the trip detail page"""
        self.client.force_login(self.enabled)
        report = TripReport.objects.create(
            title="Test Report",
            pub_date=dt.now().date(),
            slug="test-report",
            content="Test content.",
            privacy=TripReport.PUBLIC,
            trip=self.trip,
            user=self.enabled,
        )

        response = self.client.get(reverse("log:trip_detail", args=[self.trip.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("log:report_detail", args=[report.pk]))
        self.assertContains(response, reverse("log:report_update", args=[report.pk]))
