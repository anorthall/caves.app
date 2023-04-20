from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from logger.models import Trip, TripReport

User = get_user_model()


class PublicViewsIntegrationTests(TestCase):
    def setUp(self):
        # Reduce log level to avoid 404 error
        import logging

        logger = logging.getLogger("django.request")
        self.previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)

        self.client = Client()

        # Create a test user
        self.user = User.objects.create_user(
            email="test@user.app",
            password="password",
            username="testuser",
            name="Test",
        )
        self.user.is_active = True
        self.user.save()

        self.user.profile.bio = "This is my bio."
        self.user.profile.save()

        self.user.settings.privacy = self.user.settings.PUBLIC
        self.user.settings.save()

        # Iterate and create several trips belonging to the user
        for i in range(1, 11):
            start = timezone.make_aware(
                timezone.datetime(year=timezone.now().year, month=i, day=1)
            )
            end = start + timezone.timedelta(hours=5)
            self.user.trip_set.create(
                cave_name=f"Trip {i}",
                start=start,
                end=end,
                privacy=Trip.DEFAULT,
                vert_dist_up="100m",
            )

    def tearDown(self):
        """Reset the log level back to normal"""
        import logging

        logger = logging.getLogger("django.request")
        logger.setLevel(self.previous_level)

    def test_public_user_profile_accessible(self):
        """Test that the user profile page loads"""
        self.user.settings.privacy = self.user.settings.PUBLIC
        self.user.settings.save()
        response = self.client.get(f"/u/{self.user.username}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.profile.name)
        self.assertContains(response, self.user.profile.bio)

        # Test that the user's trips are listed
        for trip in self.user.trip_set.all():
            self.assertContains(response, trip.cave_name)

    def test_user_profile_private(self):
        """Test that the user profile page is not accessible if the user is private"""
        self.user.settings.privacy = self.user.settings.PRIVATE
        self.user.settings.save()
        response = self.client.get(f"/u/{self.user.username}/")
        self.assertEqual(response.status_code, 404)

    def test_default_privacy_trip_not_accessible_for_private_user(self):
        """Test that a trip belonging to a private user is not accessible"""
        self.user.settings.privacy = self.user.settings.PRIVATE
        self.user.settings.save()
        trip = self.user.trip_set.first()
        trip.privacy = Trip.DEFAULT
        trip.save()
        response = self.client.get(f"/u/{self.user.username}/{trip.pk}/")
        self.assertEqual(response.status_code, 404)

    def test_public_trip_for_private_user_is_accessible(self):
        """Test that a public trip belonging to a private user is accessible"""
        self.user.settings.privacy = self.user.settings.PRIVATE
        self.user.settings.save()
        trip = self.user.trip_set.first()
        trip.privacy = Trip.PUBLIC
        trip.save()
        response = self.client.get(f"/u/{self.user.username}/{trip.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, trip.cave_name)

    def test_private_trip_for_public_user_is_not_accessible(self):
        """Test that a private trip belonging to a public user is not accessible"""
        self.user.settings.privacy = self.user.settings.PUBLIC
        self.user.profile.save()
        trip = self.user.trips.first()
        trip.privacy = Trip.PRIVATE
        trip.save()
        response = self.client.get(f"/u/{self.user.username}/{trip.pk}/")
        self.assertEqual(response.status_code, 404)

    def test_incorrect_username_slug_for_valid_trip_returns_404(self):
        """Test that a url with an incorrect username slug returns a 404"""
        trip = self.user.trip_set.first()
        trip.privacy = Trip.PUBLIC
        trip.save()
        response = self.client.get(f"/u/invalid-user/{trip.pk}/")
        self.assertEqual(response.status_code, 404)

    def test_user_profile_without_bio_or_trips(self):
        """Test that the user profile page loads if the user has no bio or trips"""
        self.user.settings.privacy = self.user.settings.PUBLIC
        self.user.settings.save()

        self.user.profile.bio = ""
        self.user.profile.save()

        self.user.trips.delete()

        response = self.client.get(f"/u/{self.user.username}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.name)
        self.assertContains(
            response,
            "This is the public profile of a caves.app user who has not added any trips or a bio yet.",
        )

    def test_show_statistics_user_setting(self):
        """Test that the user profile page shows statistics if the user has the setting enabled"""
        self.user.settings.privacy = self.user.settings.PUBLIC
        self.user.settings.save()

        self.user.profile.page_title = ""
        self.user.profile.save()
        self.user.settings.show_statistics = True
        self.user.settings.save()

        response = self.client.get(f"/u/{self.user.username}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.profile.name)
        self.assertContains(response, self.user.profile.bio)

        # Test that the user's trips are listed
        for trip in self.user.trips:
            self.assertContains(response, trip.cave_name)

        # Test that the statistics are shown
        self.assertContains(response, "Total trips")
        self.assertContains(response, "Rope ascent")
        self.assertContains(response, "Rope descent")

        # Test that the statistics are not shown if diabled
        self.user.settings.show_statistics = False
        self.user.settings.save()

        response = self.client.get(f"/u/{self.user.username}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.profile.name)
        self.assertContains(response, self.user.profile.bio)

        # Test that the user's trips are listed
        for trip in self.user.trip_set.all():
            self.assertContains(response, trip.cave_name)

        # Test that the statistics are not shown
        self.assertNotContains(response, "Total trips")
        self.assertNotContains(response, "Rope ascent")
        self.assertNotContains(response, "Rope descent")

    def test_custom_profile_page_title(self):
        """Test that the user profile page uses the custom title if set"""
        self.user.settings.privacy = self.user.settings.PUBLIC
        self.user.settings.save()

        self.user.profile.page_title = "This is my custom title"
        self.user.profile.save()

        response = self.client.get(f"/u/{self.user.username}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.profile.page_title)

    def test_private_notes(self):
        """Test that notes are not shown on public trip pages if the user has notes set to private"""
        trip = self.user.trip_set.first()
        trip.privacy = Trip.PUBLIC
        trip.notes = "This is a note."
        trip.save()

        # Test that the notes are not shown if the user has notes set to private
        self.user.settings.private_notes = True
        self.user.settings.save()
        response = self.client.get(f"/u/{self.user.username}/{trip.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, trip.cave_name)
        self.assertNotContains(response, trip.notes)

        # Test that the notes are shown if the user has notes set to public
        self.user.settings.private_notes = False
        self.user.settings.save()
        response = self.client.get(f"/u/{self.user.username}/{trip.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, trip.cave_name)
        self.assertContains(response, trip.notes)

    def test_statistics_show_in_correct_units_for_user(self):
        """Test that the statistics on the user profile page are shown in the correct units"""
        self.user.settings.privacy = self.user.settings.PUBLIC
        self.user.settings.units = self.user.settings.METRIC
        self.user.settings.save()

        self.user.settings.show_statistics = True
        self.user.settings.save()

        self.user.profile.page_title = "Testing statistics unit function"
        self.user.profile.save()

        # Test that the statistics are shown in the correct metric units
        response = self.client.get(f"/u/{self.user.username}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.profile.page_title)
        self.assertContains(response, "1000m")

        # Test that the statistics are shown in the correct imperial units
        self.user.settings.units = self.user.settings.IMPERIAL
        self.user.settings.save()
        response = self.client.get(f"/u/{self.user.username}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.profile.page_title)
        self.assertContains(response, "3281ft")

    def test_public_trip_report_view(self):
        """Test that the public trip report view loads"""
        trip = self.user.trip_set.first()
        trip.privacy = Trip.PUBLIC
        trip.save()
        self.user.settings.privacy = self.user.settings.PUBLIC
        self.user.settings.save()

        # Create a trip report
        trip_report = TripReport.objects.create(
            trip=trip,
            user=self.user,
            slug="report",
            title="This is a trip report",
            pub_date=timezone.now().date(),
            content="This is the body of the trip report",
            privacy=TripReport.PUBLIC,
        )

        # Check the trip report loads
        response = self.client.get(f"/u/{self.user.username}/{trip_report.slug}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, trip_report.title)
        self.assertContains(response, trip_report.content)
        self.assertContains(response, trip_report.user.name)
        self.assertContains(response, trip_report.trip.cave_name)
        self.assertContains(response, reverse("public:user", args=[self.user.username]))
        self.assertContains(
            response, reverse("public:trip", args=[self.user.username, trip.pk])
        )

        # Make the report private and check it returns 404
        trip_report.privacy = TripReport.PRIVATE
        trip_report.save()

        response = self.client.get(f"/u/{self.user.username}/{trip_report.slug}/")
        self.assertEqual(response.status_code, 404)

        # Make the user and trip private and check the links do not appear
        self.user.settings.privacy = self.user.settings.PRIVATE
        self.user.settings.save()
        trip.privacy = Trip.PRIVATE
        trip.save()
        trip_report.privacy = TripReport.PUBLIC
        trip_report.save()

        response = self.client.get(f"/u/{self.user.username}/{trip_report.slug}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, trip_report.title)
        self.assertContains(response, trip_report.content)
        self.assertNotContains(
            response, reverse("public:user", args=[self.user.username])
        )
        self.assertNotContains(
            response, reverse("public:trip", args=[self.user.username, trip.pk])
        )

    def test_trip_report_links_appear_on_public_user_page(self):
        """Test links to trip reports appear on the public user page"""
        trip = self.user.trip_set.first()
        trip.privacy = Trip.PUBLIC
        trip.save()

        self.user.settings.privacy = self.user.settings.PUBLIC
        self.user.settings.save()

        # Create a trip report
        trip_report = TripReport.objects.create(
            trip=trip,
            user=self.user,
            slug="report",
            title="This is a trip report",
            pub_date=timezone.now().date(),
            content="This is the body of the trip report",
            privacy=TripReport.PUBLIC,
        )

        # Check the link to the trip report is contained on the user profile page
        response = self.client.get(f"/u/{self.user.username}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            reverse("public:report", args=[self.user.username, trip_report.slug]),
        )

        # Make the report private and check it does not appear
        trip_report.privacy = TripReport.PRIVATE
        trip_report.save()

        response = self.client.get(f"/u/{self.user.username}/")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(
            response,
            reverse("public:report", args=[self.user.username, trip_report.slug]),
        )

    def test_trip_report_links_on_trip_page(self):
        """Test links to trip reports appear on the trip page"""
        trip = self.user.trip_set.first()
        trip.privacy = Trip.PUBLIC
        trip.save()

        # Create a trip report
        trip_report = TripReport.objects.create(
            trip=trip,
            user=self.user,
            slug="report",
            title="This is a trip report",
            pub_date=timezone.now().date(),
            content="This is the body of the trip report",
            privacy=TripReport.PUBLIC,
        )

        # Check the link to the trip report is contained on the trip page
        response = self.client.get(f"/u/{self.user.username}/{trip.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            reverse("public:report", args=[self.user.username, trip_report.slug]),
        )

        # Make the report private and check it does not appear
        trip_report.privacy = TripReport.PRIVATE
        trip_report.save()

        response = self.client.get(f"/u/{self.user.username}/{trip.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(
            response,
            reverse("public:report", args=[self.user.username, trip_report.slug]),
        )
