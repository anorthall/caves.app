from django.test import Client, TestCase, tag
from django.urls import reverse
from users.factories import UserFactory

from ..factories import TripFactory


@tag("fast", "search", "views", "logger")
class TripSearchTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = UserFactory(is_active=True)
        for i in range(500):
            TripFactory(user=self.user, cave_name=f"Test Cave {i}")

    def test_search_results_page_loads_with_results(self):
        """Test that the search page loads with results"""
        self.client.force_login(self.user)

        response = self.client.get(reverse("log:search_results"), {"terms": "cave"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<h2 class="fs-4 mb-3">Results</h2>')

    def test_search_results_page_loads_without_results(self):
        """Test that the search page loads without results"""
        self.client.force_login(self.user)

        response = self.client.get(reverse("log:search_results"), {"terms": "foo-bar"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "No trips were found with the provided search terms."
        )

    def test_search_results_page_loads_with_no_terms(self):
        """Test that the search page loads with no terms"""
        self.client.force_login(self.user)

        response = self.client.get(reverse("log:search_results"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please correct the error(s) below.")

    def test_search_with_terms_under_three_characters(self):
        """Test that the search terms require at least three characters"""
        self.client.force_login(self.user)

        response = self.client.get(reverse("log:search_results"), {"terms": "ca"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter at least three characters.")

    def test_search_with_an_invalid_username(self):
        """Test specifying an invalid username in the search terms"""
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("log:search_results"),
            {
                "terms": "cave",
                "user": "invalid-username",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Username not found.")
