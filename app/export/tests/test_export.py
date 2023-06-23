import uuid
from datetime import datetime

from django.contrib.gis.measure import Distance
from django.test import TestCase, tag
from django.urls import reverse
from django.utils import timezone
from logger.factories import TripFactory
from users.models import CavingUser as User

from ..services import TripExporter


@tag("fast", "export", "pageload")
class ExportPageloadTestCase(TestCase):
    def setUp(self):
        user = User.objects.create_user(
            username="testuser",
            email="test@users.app",
            password="testpassword",
            name="Test User",
        )
        user.is_active = True
        user.save()
        self.user = user

        for i in range(1, 21):
            TripFactory(cave_name=f"Cave {i}", user=user)

    def test_export_index_page_loads(self):
        """Test that the export index page loads"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("export:index"))
        self.assertEqual(response.status_code, 200)

    def test_export_to_csv(self):
        """Test exporting a CSV file"""
        self.client.force_login(self.user)
        response = self.client.post(reverse("export:index"), {"format": "csv"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertEqual(
            response["Content-Disposition"], "attachment; filename=trips.csv"
        )

    def test_export_to_json(self):
        """Test exporting a JSON file"""
        self.client.force_login(self.user)
        response = self.client.post(reverse("export:index"), {"format": "json"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(
            response["Content-Disposition"], "attachment; filename=trips.json"
        )


@tag("fast", "export")
class ExportDataTestCase(TestCase):
    def test_export_with_custom_fields(self):
        """Test exporting a CSV file with custom fields added to trips/user"""
        # Add custom fields to user and trip
        user = User.objects.create_user(
            username="testuser2",
            email="test2@users.app",
            password="testpassword",
            name="Test User",
        )
        user.is_active = True
        user.custom_field_1_label = "Test Field"
        user.custom_field_2_label = "Test Field 2"
        user.save()

        for i in range(0, 20):
            TripFactory.create(user=user)

        uuids = []
        # Add custom fields to trips
        for trip in user.trips:
            u1, u2 = str(uuid.uuid4()), str(uuid.uuid4())
            trip.custom_field_1 = u1
            trip.custom_field_2 = u2
            trip.save()
            uuids.append((u1, u2))

        self.client.force_login(user)
        response = self.client.post(reverse("export:index"), {"format": "csv"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertContains(response, "Test Field")
        self.assertContains(response, "Test Field 2")

        for u1, u2 in uuids:
            self.assertContains(response, u1)
            self.assertContains(response, u2)

    def test_all_data_exported(self):
        """Test that all data is exported"""
        user = User.objects.create_user(
            username="testuser2",
            email="test2@users.app",
            password="testpassword",
            name="Test User",
        )
        user.is_active = True
        user.custom_field_1_label = "Test Field"
        user.custom_field_2_label = "Test Field 2"
        user.save()

        for i in range(0, 20):
            TripFactory.create(user=user)

        self.client.force_login(user)
        response = self.client.post(reverse("export:index"), {"format": "csv"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")

        for field in TripExporter.fields:
            for trip in user.trips:
                value = getattr(trip, field)
                if not value:
                    continue

                if isinstance(value, datetime):
                    value = timezone.localtime(value).strftime("%Y-%m-%d %H:%M:%S")

                if isinstance(value, Distance):
                    value = value.m

                self.assertContains(response, value)
