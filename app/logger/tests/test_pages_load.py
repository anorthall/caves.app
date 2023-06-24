from django.contrib.auth import get_user_model
from django.test import Client, TestCase, tag
from django.urls import reverse
from django.utils import timezone
from logger.models import Trip, TripReport

User = get_user_model()


@tag("fast", "views", "logger")
class TestLoggerPagesLoad(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@caves.app",
            username="testuser",
            password="password",
            name="Test User",
        )
        self.user.is_active = True
        self.user.save()

        self.trip = Trip.objects.create(
            user=self.user, cave_name="Test Trip", start=timezone.now()
        )

        self.report = TripReport.objects.create(
            user=self.user,
            trip=self.trip,
            title="Test Report",
            slug="test",
            content="Test Report Content",
            pub_date=timezone.now().date(),
        )

        self.client = Client()

    def test_index_page_loads(self):
        """Test that the home page loads"""
        response = self.client.get(reverse("log:index"))
        self.assertEqual(response.status_code, 200)

    def test_new_user_index_page_loads(self):
        """Test that the home page loads for a new user"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("log:index"))
        self.assertEqual(response.status_code, 200)

    def test_established_user_index_page_loads(self):
        """Test that the home page loads for an established user"""
        self.client.force_login(self.user)
        for i in range(50):
            Trip.objects.create(
                user=self.user, cave_name="Test Trip {}".format(i), start=timezone.now()
            ).save()

        response = self.client.get(reverse("log:index"))
        self.assertEqual(response.status_code, 200)

    def test_user_trip_list_page_loads(self):
        """Test that the user trip list page loads"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("log:user", args=[self.user.username]))
        self.assertEqual(response.status_code, 200)

    def test_user_trip_list_page_loads_with_trips(self):
        """Test that the user trip list page loads with trips"""
        self.client.force_login(self.user)
        for i in range(250):
            t = Trip.objects.create(
                cave_name=f"Test Trip {i}", start=timezone.now(), user=self.user
            )
            t.save()
        response = self.client.get(reverse("log:user", args=[self.user.username]))
        self.assertEqual(response.status_code, 200)

    def test_trip_detail_page_loads(self):
        """Test that the trip detail page loads"""
        self.client.force_login(self.user)
        response = self.client.get(self.trip.get_absolute_url())
        self.assertEqual(response.status_code, 200)

    def test_trip_update_page_loads(self):
        """Test that the trip update page loads"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("log:trip_update", args=[self.trip.uuid]))
        self.assertEqual(response.status_code, 200)

    def test_trip_list_redirect_page_loads(self):
        """Test that the trip list redirect page loads"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("log:trip_list"), follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("log:user", args=[self.user.username]))

    def test_export_page_loads(self):
        """Test that the export page loads"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("export:index"))
        self.assertEqual(response.status_code, 200)

    def test_trip_report_detail_page_loads(self):
        """Test that the trip report detail page loads"""
        self.client.force_login(self.user)
        response = self.client.get(self.report.get_absolute_url())
        self.assertEqual(response.status_code, 200)

    def test_trip_report_update_page_loads(self):
        """Test that the trip report update page loads"""
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("log:report_update", args=[self.report.trip.uuid])
        )
        self.assertEqual(response.status_code, 200)

    def test_htmx_feed_page_loads(self):
        """Test that the HTMX feed page loads"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("log:feed_htmx_view"))
        self.assertEqual(response.status_code, 200)

    def test_htmx_trip_like_toggle_page_loads(self):
        """Test that the HTMX trip like toggle page loads"""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("log:trip_like_htmx_view", args=[self.trip.uuid])
        )
        self.assertEqual(response.status_code, 200)

    def test_htmx_trip_like_toggle_page_loads_with_likes(self):
        """Test that the HTMX trip like toggle page loads with likes"""
        self.client.force_login(self.user)
        self.trip.likes.add(self.user)
        response = self.client.post(
            reverse("log:trip_like_htmx_view", args=[self.trip.uuid])
        )
        self.assertEqual(response.status_code, 200)

    def test_hours_per_month_chart_page_loads(self):
        """Test that the hours per month chart page loads"""
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("stats:chart_hours_per_month", args=[self.user.username])
        )
        self.assertEqual(response.status_code, 200)

    def test_stats_over_time_chart_page_loads(self):
        """Test that the stats over time chart page loads"""
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("stats:chart_stats_over_time", args=[self.user.username])
        )
        self.assertEqual(response.status_code, 200)

    def test_trip_types_chart_page_loads(self):
        """Test that the trip types chart page loads"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("stats:chart_trip_types"))
        self.assertEqual(response.status_code, 200)

    def test_trip_types_over_time_chart_page_loads(self):
        """Test that the trip types over time chart page loads"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("stats:chart_trip_types_time"))
        self.assertEqual(response.status_code, 200)

    @tag("search")
    def test_search_page_loads(self):
        """Test that the search page loads"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("log:search"))
        self.assertEqual(response.status_code, 200)
