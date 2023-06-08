from django.contrib.auth import get_user_model
from django.test import Client, TestCase, tag
from django.urls import reverse
from django.utils import timezone as tz
from django.utils.timezone import timedelta as td

from ..factories import TripFactory
from ..models import Trip, TripReport

User = get_user_model()


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
            self.assertContains(response, reverse("log:trip_update", args=[trip.uuid]))

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
        self.user.page_title = "Test Page Title 123"
        self.user.save()

        response = self.client.get(reverse("log:user", args=[self.user.username]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Page Title 123")

    def test_user_profile_page_bio(self):
        """Test the user profile page bio"""
        self.client.force_login(self.user)
        self.user.bio = "Test bio 123"
        self.user.save()

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

        self.user.friends.add(self.user2)
        self.user2.friends.add(self.user)

        self.client.force_login(self.user2)
        response = self.client.get(reverse("log:user", args=[self.user.username]))
        self.assertEqual(response.status_code, 200)

        for trip in self.user.trips.order_by("-start")[:50]:
            self.assertContains(response, trip.cave_name)

    def test_that_private_trips_do_not_appear_in_the_trip_feed(self):
        """Test that private trips do not appear in the trip feed"""
        self.client.force_login(self.user2)
        self.user.friends.add(self.user2)
        self.user2.friends.add(self.user)

        # Delete all user2 trips so they don't appear in the feed
        # and block user1 trips from appearing
        for trip in self.user2.trips:
            trip.delete()

        # First set the trips to public and verify they do appear in the
        # feed, otherwise if sorting is broken the test will pass even if
        # private trips are appearing in the feed
        for trip in self.user.trips:
            trip.privacy = Trip.PUBLIC
            trip.save()

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

    def test_user_profile_page_with_various_privacy_settings(self):
        """Test the user profile page with various privacy settings"""
        self.client.force_login(self.user2)
        response = self.client.get(reverse("log:user", args=[self.user.username]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.username)

        self.user.privacy = User.PRIVATE
        self.user.save()
        response = self.client.get(reverse("log:user", args=[self.user.username]))
        self.assertEqual(response.status_code, 403)

        self.user.privacy = User.FRIENDS
        self.user.save()
        response = self.client.get(reverse("log:user", args=[self.user.username]))
        self.assertEqual(response.status_code, 403)

        self.user.friends.add(self.user2)
        self.user2.friends.add(self.user)
        response = self.client.get(reverse("log:user", args=[self.user.username]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.username)

        self.user.privacy = User.PUBLIC
        self.user.save()
        response = self.client.get(reverse("log:user", args=[self.user.username]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.username)

        self.client.logout()
        self.user.privacy = User.PRIVATE
        self.user.save()
        response = self.client.get(reverse("log:user", args=[self.user.username]))
        self.assertEqual(response.status_code, 403)

        self.user.privacy = User.FRIENDS
        self.user.save()
        response = self.client.get(reverse("log:user", args=[self.user.username]))
        self.assertEqual(response.status_code, 403)

        self.user.privacy = User.PUBLIC
        self.user.save()
        response = self.client.get(reverse("log:user", args=[self.user.username]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.username)

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
            pub_date=tz.now().date(),
        )
        response = self.client.get(trip.get_absolute_url())
        self.assertContains(response, report.get_absolute_url())

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
        response = self.client.get(trip.get_absolute_url())
        self.assertNotContains(response, report.get_absolute_url())

    def test_htmx_like_view_on_an_object_the_user_cannot_view(self):
        """Test that the HTMX like view respects privacy"""
        trip = Trip.objects.filter(user=self.user).first()
        self.client.force_login(self.user2)

        trip.privacy = Trip.PRIVATE
        trip.save()

        response = self.client.post(
            reverse("log:trip_like_htmx_view", args=[trip.uuid]),
        )
        self.assertEqual(response.status_code, 403)

    def test_notification_redirect_view_as_invalid_user(self):
        """Test that the notification redirect view returns a 403 for an invalid user"""
        self.client.force_login(self.user2)
        notification = self.user.notify("Test notification", "/")
        response = self.client.get(
            reverse("users:notification", args=[notification.pk]),
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(notification.read, False)

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
        response = self.client.get(report.get_absolute_url())
        self.assertEqual(response.status_code, 403)

        report.privacy = TripReport.FRIENDS
        report.save()
        response = self.client.get(report.get_absolute_url())
        self.assertEqual(response.status_code, 403)

        self.user.friends.add(self.user2)
        self.user2.friends.add(self.user)
        response = self.client.get(report.get_absolute_url())
        self.assertEqual(response.status_code, 200)

        report.privacy = TripReport.PUBLIC
        report.save()
        response = self.client.get(report.get_absolute_url())
        self.assertEqual(response.status_code, 200)

        report.privacy = TripReport.DEFAULT
        report.save()
        trip.privacy = Trip.FRIENDS
        trip.save()
        response = self.client.get(report.get_absolute_url())
        self.assertEqual(response.status_code, 200)

        trip.privacy = Trip.PRIVATE
        trip.save()
        response = self.client.get(report.get_absolute_url())
        self.assertEqual(response.status_code, 403)

        trip.privacy = Trip.PUBLIC
        trip.save()
        response = self.client.get(report.get_absolute_url())
        self.assertEqual(response.status_code, 200)

    def test_public_statistics_privacy_setting(self):
        """Test that the public statistics privacy setting works"""
        for i in range(0, 50):
            TripFactory(user=self.user)
        self.user.public_statistics = False
        self.user.save()

        response = self.client.get(self.user.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '<div class="profile-stats')

        self.user.public_statistics = True
        self.user.save()

        response = self.client.get(self.user.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<div class="profile-stats')
