from django.test import Client, TestCase, tag
from django.urls import reverse
from logger.factories import TripFactory

from ..factories import UserFactory


@tag("fast", "trips", "custom_fields")
class CustomFieldTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = UserFactory(is_active=True)
        self.trip = TripFactory(user=self.user)

    def test_submitting_custom_field_value(self):
        """Test that a custom field value can be submitted via a POST request."""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("users:custom_fields_update"),
            {
                "custom_field_1_label": "Test Label",
            },
            follow=True,
        )

        self.user.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.user.custom_field_1_label, "Test Label")
        self.assertContains(response, "Your custom fields have been updated.")

    def test_submitting_custom_field_value_when_a_trip_holds_that_value(self):
        """Test validation of custom field form when a trip holds that value."""
        self.user.custom_field_1_label = "Test Label"
        self.trip.custom_field_1 = "Test Value"
        self.user.save()
        self.trip.save()

        self.client.force_login(self.user)
        response = self.client.post(
            reverse("users:custom_fields_update"),
            {
                "custom_field_1_label": "Changed Label",
            },
            follow=True,
        )

        self.user.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.user.custom_field_1_label, "Test Label")
        self.assertContains(
            response,
            "This field cannot be removed or changed as some trips have a value for it",
        )

    def test_submitting_a_custom_field_value_under_three_characters(self):
        """Test validation of custom field form when a value is too short."""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("users:custom_fields_update"),
            {
                "custom_field_1_label": "XX",
            },
            follow=True,
        )

        self.user.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.user.custom_field_1_label, "")
        self.assertContains(response, "The field name must be at least 3 characters long")

    def test_that_custom_fields_appear_on_the_trip_add_form(self):
        """Test that custom fields appear on the trip add form."""
        self.user.custom_field_1_label = "CustomFieldABCDEFG"
        self.user.save()

        self.client.force_login(self.user)
        response = self.client.get(reverse("log:trip_create"))

        self.assertContains(response, "CustomFieldABCDEFG")

    def test_that_custom_fields_appear_on_the_trip_detail_page(self):
        """Test that custom fields appear on the trip detail page."""
        self.user.custom_field_1_label = "CustomFieldABCDEFG"
        self.user.save()

        self.trip.custom_field_1 = "CustomFieldValue"
        self.trip.save()

        self.client.force_login(self.user)
        response = self.client.get(self.trip.get_absolute_url())

        self.assertContains(response, "CustomFieldABCDEFG")
        self.assertContains(response, "CustomFieldValue")

    def test_that_custom_fields_appear_on_the_social_feed(self):
        """Test that custom fields appear on the trip detail page."""
        self.user.custom_field_1_label = "CustomFieldABCDEFG"
        self.user.save()

        self.trip.custom_field_1 = "CustomFieldValue"
        self.trip.save()

        self.client.force_login(self.user)
        response = self.client.get(reverse("log:index"))

        self.assertContains(response, "CustomFieldABCDEFG")
        self.assertContains(response, "CustomFieldValue")

    def test_loading_a_trip_with_custom_field_data_without_a_label(self):
        """Test that custom fields appear on the trip detail page."""
        self.trip.custom_field_1 = "CustomFieldValue"
        self.trip.save()

        self.client.force_login(self.user)
        response = self.client.get(self.trip.get_absolute_url())

        self.assertNotContains(response, "CustomFieldValue")
