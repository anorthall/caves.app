from unittest.mock import MagicMock

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, tag
from django.urls import reverse
from django.utils import timezone

from .. import feed
from ..models import Trip

User = get_user_model()


@tag("social", "fast", "integration")
class FeedIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="test1@user.app", username="test1", name="Test User 1"
        )
        self.user.is_active = True
        self.user.save()

        self.user2 = User.objects.create_user(
            email="test2@users.app", username="test2", name="Test User 2"
        )
        self.user2.is_active = True
        self.user2.save()

    def test_new_user_page_is_displayed(self):
        """Test that the new user page is displayed when there are no trips"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("log:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "This notice will disappear once there are trips to display in your feed.",
        )

    def test_load_more_trips_button_is_displayed(self):
        """Test that the load more trips button is displayed"""
        self.client.force_login(self.user)
        for i in range(1, 12):
            Trip.objects.create(
                user=self.user, cave_name=f"Test Cave {i}", start=timezone.now()
            )

        response = self.client.get(reverse("log:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<div id="loadMoreTrips"')

    def test_load_more_trips_button_is_not_displayed(self):
        """Test that the load more trips button is not displayed"""
        self.client.force_login(self.user)
        for i in range(1, 6):
            Trip.objects.create(
                user=self.user, cave_name=f"Test Cave {i}", start=timezone.now()
            )

        response = self.client.get(reverse("log:index"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '<div id="loadMoreTrips"')

    def test_feed_ordering_by_trip_start(self):
        """Test that the feed is ordered by trip start when selected"""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("log:feed_set_ordering"), {"sort": User.FEED_DATE}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("log:index"))

        self.user.refresh_from_db()
        self.assertEqual(self.user.feed_ordering, User.FEED_DATE)

        for i in range(1, 6):
            Trip.objects.create(
                user=self.user,
                cave_name=f"Test Cave {i}",
                start=timezone.now() - timezone.timedelta(days=i),
            )

        response = self.client.get(reverse("log:index"))
        self.assertEqual(response.status_code, 200)

        first_cave_name = response.content.split(b'<h1 class="cave-name fs-4 my-1">')[
            1
        ].split(b"</h1>")[0]
        self.assertEqual(first_cave_name, b"Test Cave 1")

    def test_feed_ordering_by_trip_added(self):
        """Test that the feed is ordered by trip added when selected"""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("log:feed_set_ordering"), {"sort": User.FEED_ADDED}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("log:index"))

        self.user.refresh_from_db()
        self.assertEqual(self.user.feed_ordering, User.FEED_ADDED)

        for i in range(1, 6):
            Trip.objects.create(
                user=self.user,
                cave_name=f"Test Cave {i}",
                start=timezone.now() - timezone.timedelta(days=i),
            )

        response = self.client.get(reverse("log:index"))
        self.assertEqual(response.status_code, 200)

        first_cave_name = response.content.split(b'<h1 class="cave-name fs-4 my-1">')[
            1
        ].split(b"</h1>")[0]
        self.assertEqual(first_cave_name, b"Test Cave 5")

    def test_setting_feed_ordering_to_invalid_value(self):
        """Test that the feed ordering is not changed if an invalid value is
        provided"""
        self.user.feed_ordering = User.FEED_DATE
        self.user.save()

        self.client.force_login(self.user)
        response = self.client.post(
            reverse("log:feed_set_ordering"), {"sort": "invalid"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("log:index"))

        self.user.refresh_from_db()
        self.assertEqual(self.user.feed_ordering, User.FEED_DATE)


@tag("social", "fast", "unit")
class FeedUnitTests(TestCase):
    def test_get_trips_context_with_a_user_without_trips(self):
        """Test the get_trips_context method with a user without trips"""
        user = User.objects.create_user(
            email="test@user.app", username="test", name="Test User"
        )
        request = MagicMock()
        request.user = user
        result = feed.get_trips_context(request, User.FEED_DATE)
        self.assertEqual(result, [])
