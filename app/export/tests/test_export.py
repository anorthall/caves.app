import uuid
from datetime import datetime

from django.contrib.gis.measure import Distance
from django.core.exceptions import FieldDoesNotExist
from django.test import TestCase, tag
from django.urls import reverse
from django.utils import timezone
from logger.factories import TripFactory
from logger.models import Trip
from users.models import CavingUser as User

from ..services import Exporter, TripExporter


@tag("fast", "export", "pageload")
class ExportPageloadTests(TestCase):
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

    def test_export_with_invalid_format(self):
        """Test exporting with an invalid format"""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("export:index"), {"format": "invalid"}, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "There was an error generating your download.",
        )


@tag("fast", "export")
class ExportDataTests(TestCase):
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

                if field == "cavers":
                    value = ", ".join([str(v) for v in value.all()])

                self.assertContains(response, value)


@tag("exporter", "export", "fast")
class ExporterTests(TestCase):
    def test_exporter_get_distance_units_method(self):
        """Test that the get_distance_units method returns the units property"""
        exporter = Exporter(Trip.objects.none())
        self.assertEqual(exporter._get_distance_units(), exporter.distance_units)

    def test_exporter_format_distancefield_method(self):
        """Test that the format_df method returns the distance in the correct units"""
        exporter = Exporter(Trip.objects.none())

        exporter.distance_units = "m"
        self.assertEqual(exporter._format_distancefield(Distance(m=100)), "100.0")

        exporter.distance_units = "km"
        self.assertEqual(exporter._format_distancefield(Distance(m=100)), "0.1")

        exporter.distance_units = "invalid"
        self.assertEqual(exporter._format_distancefield(Distance(m=100)), "100.0")

    def test_exporter_distancefield_header(self):
        """Test that the distancefield_header method returns the correct header"""
        exporter = Exporter(Trip.objects.none())
        exporter.model = Trip

        exporter.distance_units = "m"
        self.assertEqual(
            exporter._get_distancefield_header("vert_dist_up"),
            "Rope ascent distance (m)",
        )

        exporter.distance_units = "km"
        self.assertEqual(
            exporter._get_distancefield_header("vert_dist_up"),
            "Rope ascent distance (km)",
        )

        exporter.distance_units = "ft"
        self.assertEqual(
            exporter._get_distancefield_header("vert_dist_up"),
            "Rope ascent distance (ft)",
        )

    def test_exporter_get_field_header_method(self):
        """Test that the get_field_header method returns the correct header"""
        exporter = Exporter(Trip.objects.none())
        exporter.model = Trip

        self.assertEqual(exporter._get_field_header("cave_name"), "Cave name")

        def _get_cave_name_header():
            return "Test Header"

        exporter._get_cave_name_header = _get_cave_name_header
        self.assertEqual(exporter._get_field_header("cave_name"), "Test Header")

        with self.assertRaises(FieldDoesNotExist):
            self.assertEqual(
                exporter._get_field_header("invalid_field"), "Invalid field"
            )


@tag("exporter", "tripexporter", "export", "fast")
class TripExporterTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@user.app",
            password="testpassword",
            name="Test User",
        )
        self.user.is_active = True
        self.user.save()

        self.trip = TripFactory.create(user=self.user)

    def test_trip_exporter_get_distance_units_method(self):
        """Test that the get_distance_units method returns the units property"""
        exporter = TripExporter(self.user, Trip.objects.all())
        self.assertEqual(self.user.units, User.METRIC)
        self.assertEqual(exporter._get_distance_units(), "m")

        self.user.units = User.IMPERIAL
        self.user.save()

        exporter = TripExporter(self.user, Trip.objects.all())
        self.assertEqual(exporter._get_distance_units(), "ft")
