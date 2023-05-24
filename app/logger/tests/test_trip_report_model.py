import logging

from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from django.test import Client, TestCase, tag
from django.urls import reverse
from django.utils import timezone as tz
from django.utils.timezone import datetime as dt

from ..models import Trip, TripReport

User = get_user_model()


@tag("logger", "tripreport", "fast", "integration")
class TripReportIntegrationTests(TestCase):
    def setUp(self):
        """Reduce log level to avoid 404 error"""
        logger = logging.getLogger("django.request")
        self.previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)

        self.client = Client()

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

        response = self.client.post(reverse("log:report_delete", args=[report.pk]))
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

        response = self.client.post(reverse("log:report_delete", args=[report.pk]))
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
