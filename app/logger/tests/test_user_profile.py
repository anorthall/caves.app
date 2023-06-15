from django.contrib.auth import get_user_model
from django.test import Client, TestCase, tag
from django.urls import reverse
from django.utils import timezone as tz
from django.utils.timezone import timedelta as td

from ..factories import TripFactory
from ..models import Trip

User = get_user_model()


@tag("fast", "profile", "logger", "views")
class UserProfileViewTests(TestCase):
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

        self.user3 = User.objects.create_user(
            email="user3@caves.app",
            username="user3",
            password="password",
            name="User 3 Name",
        )
        self.user3.is_active = True
        self.user3.privacy = User.PUBLIC
        self.user3.save()

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

    @tag("privacy")
    def test_private_trips_do_not_appear_on_profile_page_trip_list(self):
        """Test that private trips do not appear on the user profile page"""
        for trip in self.user.trips:
            trip.privacy = Trip.PRIVATE
            trip.save()

        self.client.force_login(self.user2)
        response = self.client.get(reverse("log:user", args=[self.user.username]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "User1 Cave")

    @tag("privacy")
    def test_friend_only_trips_do_not_appear_on_profile_page_trip_list(self):
        """Test that friend only trips do not appear on the user profile page"""
        for trip in self.user.trips:
            trip.privacy = Trip.FRIENDS
            trip.save()

        self.client.force_login(self.user2)
        response = self.client.get(reverse("log:user", args=[self.user.username]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "User1 Cave")

    @tag("privacy")
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

    @tag("privacy")
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

    @tag("privacy")
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

    def test_friends_appear_on_the_user_profile_page(self):
        """Test that friends appear on the user profile page when viewed by the user"""
        self.client.force_login(self.user)
        response = self.client.get(self.user.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.user2.get_absolute_url())
        self.assertNotContains(response, self.user3.get_absolute_url())

        for user in [self.user2, self.user3]:
            self.user.friends.add(user)
            user.friends.add(self.user)

        response = self.client.get(self.user.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user2.get_absolute_url())
        self.assertContains(response, self.user3.get_absolute_url())

    def test_mutual_friends_appear_on_the_user_profile_page(self):
        """Test that mutual friends appear on the user profile page"""
        self.client.force_login(self.user)

        self.user2.friends.add(self.user3)
        self.user3.friends.add(self.user2)

        response = self.client.get(self.user2.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.user3.get_absolute_url())

        self.user.friends.add(self.user3)
        self.user3.friends.add(self.user)

        response = self.client.get(self.user2.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user3.get_absolute_url())

    @tag("privacy")
    def test_no_friends_appear_for_an_unauthenticated_user(self):
        """Test that no friends appear on the user profile page when not logged in"""
        for user in [self.user2, self.user3]:
            self.user.friends.add(user)
            user.friends.add(self.user)

        response = self.client.get(self.user.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.user2.get_absolute_url())
        self.assertNotContains(response, self.user3.get_absolute_url())
        self.assertNotContains(response, "Friends")
