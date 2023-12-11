import uuid
from unittest.mock import MagicMock

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, tag
from django.urls import reverse
from django.utils import timezone

from .. import services
from ..factories import TripFactory
from ..models import Trip

User = get_user_model()


@tag("feed", "fast", "views")
class SocialFeedTests(TestCase):
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
        for _ in range(1, 12):
            TripFactory(user=self.user)

        response = self.client.get(reverse("log:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<div id="loadMoreTrips"')

    def test_load_more_trips_button_is_not_displayed(self):
        """Test that the load more trips button is not displayed"""
        self.client.force_login(self.user)
        for _ in range(1, 6):
            TripFactory(user=self.user)

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

    def test_get_trips_context_with_a_user_without_trips(self):
        """Test the get_trips_context method with a user without trips"""
        user = User.objects.create_user(
            email="test@user.app", username="test", name="Test User"
        )
        request = MagicMock()
        request.user = user
        result = services.get_trips_context(request, User.FEED_DATE)
        self.assertEqual(result, [])

    @tag("privacy")
    def test_that_private_trips_do_not_appear_in_the_trip_feed(self):
        """Test that private trips do not appear in the trip feed"""
        self.client.force_login(self.user2)
        self.user.friends.add(self.user2)
        self.user2.friends.add(self.user)

        for _ in range(1, 50):
            TripFactory(user=self.user, cave_name="User1 Cave", privacy=Trip.PUBLIC)

        response = self.client.get(reverse("log:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "User1 Cave")

        # Now set the trips to private and verify they do not appear in the feed
        for trip in self.user.trips:
            trip.privacy = Trip.PRIVATE
            trip.save()

        response = self.client.get(reverse("log:index"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "User1 Cave")

    @tag("privacy", "htmx")
    def test_htmx_trip_like_view_on_an_object_the_user_cannot_view(self):
        """Test that the HTMX like view respects privacy"""
        trip = TripFactory(user=self.user, privacy=Trip.PRIVATE)
        self.client.force_login(self.user2)

        response = self.client.post(
            reverse("log:trip_like_htmx_view", args=[trip.uuid]),
        )
        self.assertEqual(response.status_code, 403)

    @tag("htmx")
    def test_htmx_trip_like_view_on_an_invalid_uuid(self):
        """Test that the HTMX like view returns a 404 on an invalid UUID"""
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("log:trip_like_htmx_view", args=[uuid.uuid4()]),
        )
        self.assertEqual(response.status_code, 404)
