import csv
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from distancefield import D
from django.core.files.base import ContentFile
from django.test import TestCase, tag
from django.urls import reverse
from logger.models import Trip
from users.models import CavingUser as User

from ..services import FIELD_MAP, get_formset_with_data, get_headers


@tag("fast", "import")
class ImportTests(TestCase):
    def setUp(self):
        self.base_path = os.path.dirname(__file__)

        self.user = User.objects.create_user(
            username="testuser",
            email="test@user.app",
            password="testpassword",
            name="Test User",
        )
        self.user.is_active = True
        self.user.save()

        self.client.force_login(self.user)

    @tag("pageload")
    def test_import_index_page_loads(self):
        """Test that the import index page loads"""
        response = self.client.get(reverse("import:index"))
        self.assertEqual(response.status_code, 200)

    def test_import_sample_csv(self):
        """Test that the import sample CSV contains the correct data"""
        response = self.client.get(reverse("import:sample"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        for k, v in FIELD_MAP:
            self.assertIn(v, response.content.decode())

    def test_upload_csv_with_no_file(self):
        """Test uploading a CSV file with no file"""
        response = self.client.post(reverse("import:process"), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Unable to process the uploaded file.")

    def test_upload_csv_with_invalid_file(self):
        """Test uploading a CSV file with an invalid file"""
        response = self.client.post(
            reverse("import:process"), {"file": "invalid"}, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Unable to process the uploaded file.")

    def test_upload_csv_with_empty_file(self):
        """Test uploading an empty file"""
        path = os.path.join(self.base_path, "test_csvs/empty_file.csv")
        with open(path, "rb") as f:
            file = ContentFile(f.read(), name="empty_file.csv")

        response = self.client.post(
            reverse("import:process"), {"file": file}, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Unable to process the uploaded file.")

    def test_upload_csv_with_file_with_no_data(self):
        """Test uploading a CSV file with no data"""
        path = os.path.join(self.base_path, "test_csvs/no_data.csv")
        with open(path, "rb") as f:
            file = ContentFile(f.read(), name="no_data.csv")

        response = self.client.post(
            reverse("import:process"), {"file": file}, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Unable to process the uploaded file.")

    def test_upload_csv_with_file_with_too_much_data(self):
        """Test uploading a CSV file with too much data"""
        path = os.path.join(self.base_path, "test_csvs/too_many_rows.csv")
        with open(path, "rb") as f:
            file = ContentFile(f.read(), name="too_many_rows.csv")

        response = self.client.post(
            reverse("import:process"), {"file": file}, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Unable to process the uploaded file.")

    def test_upload_csv_with_file_with_blank_rows(self):
        """Test that blank rows are ignored"""
        path = os.path.join(self.base_path, "test_csvs/blank_rows.csv")
        with open(path, "rb") as f:
            file = ContentFile(f.read(), name="blank_rows.csv")

        response = self.client.post(
            reverse("import:process"), {"file": file}, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "45 trips have been found.")

    def test_upload_with_a_json_file(self):
        """Test that a non-CSV file is rejected"""
        path = os.path.join(self.base_path, "test_csvs/not_a_csv_file.json")
        with open(path, "rb") as f:
            file = ContentFile(f.read(), name="not_a_csv_file.json")

        response = self.client.post(
            reverse("import:process"), {"file": file}, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Unable to process the uploaded file.")

    def test_upload_with_a_valid_file(self):
        """Test that a valid CSV file is processed"""
        path = os.path.join(self.base_path, "test_csvs/valid_trips.csv")
        with open(path, "rb") as f:
            file = ContentFile(f.read(), name="valid_trips.csv")

        response = self.client.post(
            reverse("import:process"), {"file": file}, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "3 trips have been found.")
        self.assertContains(response, "County Pot")
        self.assertContains(response, "Lancaster Hole")
        self.assertContains(response, "Ireby Fell Cavern")
        self.assertContains(response, "Andrew Northall")
        self.assertContains(response, 'value="2022-06-17 12:00:00"')

    def test_save_with_no_data(self):
        """Test that the save view returns an error when no data is sent"""
        response = self.client.post(reverse("import:save"), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Not all fields have been completed and/or some fields have errors.",
        )

    def test_save_with_valid_data(self):
        """Test saving data with valid data"""
        path = os.path.join(self.base_path, "test_csvs/valid_trips.csv")
        with open(path, "rb") as f:
            test_data = csv.DictReader(
                f.read().decode("UTF-8").splitlines(), fieldnames=get_headers()
            )

        next(test_data)  # Skip the header row
        rows = list(test_data)

        data = get_formset_with_data(rows, data_only=True)

        response = self.client.post(reverse("import:save"), data, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Successfully imported 3 trips!")

        # Check that the trips have been created
        self.assertEqual(Trip.objects.count(), 3)

        # Check that the trips have the correct data
        trip = Trip.objects.get(cave_name="Trip 1")
        self.assertEqual(trip.cave_entrance, "Lancaster Hole")
        self.assertEqual(trip.cave_exit, "County Pot")
        self.assertEqual(
            trip.start, datetime(2022, 6, 17, 11, 0, 0, tzinfo=ZoneInfo("UTC"))
        )
        self.assertEqual(
            trip.end, datetime(2022, 6, 17, 17, 0, 0, tzinfo=ZoneInfo("UTC"))
        )
        self.assertEqual(trip.cavers, "Andrew Northall")

        trip = Trip.objects.get(cave_name="Trip 2")
        self.assertEqual(trip.privacy, Trip.DEFAULT)
        self.assertEqual(trip.horizontal_dist, D(m=500))

        trip = Trip.objects.get(cave_name="Trip 3")
        self.assertEqual(
            trip.start, datetime(2022, 6, 20, 15, 0, 0, tzinfo=ZoneInfo("UTC"))
        )
