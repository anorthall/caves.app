import uuid

from django.test import Client, TestCase, tag
from django.urls import reverse
from users.factories import UserFactory

from ..factories import TripFactory
from ..models import Trip


@tag("fast", "search", "views", "logger")
class TripSearchTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = UserFactory(is_active=True)
        self.user2 = UserFactory(is_active=True)
        for i in range(100):
            TripFactory(user=self.user, cave_name=f"Test Cave {i}")

    def test_search_page_loads_with_results(self):
        """Test that the search page loads with results"""
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("log:search"),
            {
                "terms": "cave",
                "trip_type": "Any",
            },
        )

        self.assertEqual(response.status_code, 200)

    def test_no_search_results_message_is_displayed(self):
        """Test that the search page displays the no results found message"""
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("log:search"),
            {
                "terms": "foo-bar",
                "trip_type": "Any",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "No trips were found with the provided search terms."
        )

    def test_search_with_terms_under_three_characters(self):
        """Test that the search terms require at least three characters"""
        self.client.force_login(self.user)

        response = self.client.post(reverse("log:search"), {"terms": "ca"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter at least three characters.")

    def test_search_with_an_invalid_username(self):
        """Test specifying an invalid username in the search terms"""
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("log:search"),
            {
                "terms": "cave",
                "user": "invalid-username",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Username not found.")

    @tag("privacy")
    def test_private_trips_do_not_appear_in_search_results(self):
        """Test that private trips do not appear in search results"""
        self.client.force_login(self.user2)

        # First check the trip appears when the trip is public
        test_finder = str(uuid.uuid4())
        test_identifier = str(uuid.uuid4())
        trip = TripFactory(
            user=self.user, cave_name=test_finder, cave_entrance=test_identifier
        )
        trip.privacy = Trip.PUBLIC
        trip.save()

        response = self.client.post(
            reverse("log:search"),
            {
                "terms": test_finder,
                "trip_type": "Any",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, test_identifier)
        self.assertContains(response, trip.get_absolute_url())

        # Now check the trip does not appear when private trips is enabled
        trip.privacy = Trip.PRIVATE
        trip.save()

        response = self.client.post(
            reverse("log:search"),
            {
                "terms": test_finder,
                "trip_type": "Any",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, trip.get_absolute_url())
        self.assertNotContains(response, test_identifier)

    def test_private_trips_appear_in_results_when_searching_own_trips(self):
        """Test that private trips appear in search results when searching own trips"""
        self.client.force_login(self.user)

        test_finder = str(uuid.uuid4())
        test_identifier = str(uuid.uuid4())
        trip = TripFactory(
            user=self.user, cave_name=test_finder, cave_entrance=test_identifier
        )

        trip.privacy = Trip.PRIVATE
        trip.save()

        response = self.client.post(
            reverse("log:search"),
            {
                "terms": test_finder,
                "trip_type": "Any",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, trip.get_absolute_url())
        self.assertContains(response, test_identifier)

    def test_search_with_trip_type(self):
        """Test that the search page displays the no results found message"""
        self.client.force_login(self.user)

        # First check that the trip is found when searching for the trip type
        trip = TripFactory(user=self.user, type="Sport")

        response = self.client.post(
            reverse("log:search"),
            {
                "terms": trip.cave_name,
                "trip_type": "Sport",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, trip.get_absolute_url())

        # Now check that the trip is not found when searching for a different trip type
        response = self.client.post(
            reverse("log:search"),
            {
                "terms": trip.cave_name,
                "trip_type": "Exploration",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, trip.get_absolute_url())

    def test_search_by_username(self):
        """Test that searching by username shows trips by that user only"""
        self.client.force_login(self.user)

        # First check that the trip is found when searching for the username
        trip = TripFactory(user=self.user2, privacy=Trip.PUBLIC)

        response = self.client.post(
            reverse("log:search"),
            {
                "terms": trip.cave_name,
                "user": trip.user.username,
                "trip_type": "Any",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, trip.get_absolute_url())

        # Now check that the trip is not found when searching for a different username
        response = self.client.post(
            reverse("log:search"),
            {
                "terms": trip.cave_name,
                "user": self.user.username,
                "trip_type": "Any",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, trip.get_absolute_url())

    def test_search_result_pagination(self):
        """Test search result pagniation"""
        self.client.force_login(self.user)

        # Create 11 trips
        for i in range(11):
            TripFactory(
                user=self.user,
                cave_name=f"Pagination Test {i}",
                cave_entrance="Testing Pagination",
            )

        # Check that the first page contains 10 trips
        response = self.client.post(
            reverse("log:search"),
            {
                "terms": "Pagination Test",
                "trip_type": "Any",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "?page=2")

        # Check that the second page contains 1 trip
        response = self.client.get(f"{reverse('log:search')}?page=2")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Testing Pagination")
