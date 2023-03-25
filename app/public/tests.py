from django.test import TestCase, Client
from django.utils import timezone
from django.contrib.auth import get_user_model
from logger.models import Trip


class PublicViewsIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Create a test user
        self.user = get_user_model().objects.create_user(
            email="test@user.app",
            password="password",
            username="testuser",
            first_name="Test",
            last_name="User",
        )
        self.user.bio = "This is my bio."
        self.user.is_active = True
        self.user.privacy = get_user_model().PUBLIC
        self.user.save()

        # Iterate and create several trips belonging to the user
        for i in range(1, 10):
            start = timezone.make_aware(timezone.datetime(year=2020, month=i, day=1))
            end = start + timezone.timedelta(hours=5)
            self.user.trip_set.create(
                cave_name=f"Trip {i}", start=start, end=end, privacy=Trip.DEFAULT
            )

    def test_user_profile(self):
        """Test that the user profile page loads"""
        self.user.privacy = get_user_model().PUBLIC
        self.user.save()
        response = self.client.get(f"/u/{self.user.username}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.full_name)
        self.assertContains(response, self.user.bio)

        # Test that the user's trips are listed
        for trip in self.user.trip_set.all():
            self.assertContains(response, trip.cave_name)

    def test_user_profile_private(self):
        """Test that the user profile page is not accessible if the user is private"""
        self.user.privacy = get_user_model().PRIVATE
        self.user.save()
        response = self.client.get(f"/u/{self.user.username}/")
        self.assertEqual(response.status_code, 404)

    def test_trip_not_accessible_for_private_user(self):
        """Test that a trip belonging to a private user is not accessible"""
        self.user.privacy = get_user_model().PRIVATE
        self.user.save()
        trip = self.user.trip_set.first()
        trip.privacy = Trip.DEFAULT
        trip.save()
        response = self.client.get(f"/u/{self.user.username}/{trip.pk}/")
        self.assertEqual(response.status_code, 404)

    def test_public_trip_for_private_user_is_accessible(self):
        """Test that a public trip belonging to a private user is accessible"""
        self.user.privacy = get_user_model().PRIVATE
        self.user.save()
        trip = self.user.trip_set.first()
        trip.privacy = Trip.PUBLIC
        trip.save()
        response = self.client.get(f"/u/{self.user.username}/{trip.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, trip.cave_name)

    def test_private_trip_for_public_user_is_not_accessible(self):
        """Test that a private trip belonging to a public user is not accessible"""
        self.user.privacy = get_user_model().PUBLIC
        self.user.save()
        trip = self.user.trip_set.first()
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
        self.user.privacy = get_user_model().PUBLIC
        self.user.bio = ""
        self.user.save()
        self.user.trip_set.all().delete()
        response = self.client.get(f"/u/{self.user.username}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.full_name)
        self.assertContains(
            response,
            "This is the public profile of a caves.app user who has not added any trips or a bio yet.",
        )
