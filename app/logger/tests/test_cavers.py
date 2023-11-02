import logging
from datetime import datetime as dt

from django.contrib.auth import get_user_model
from django.test import TestCase, tag
from django.urls import reverse
from logger.models import Caver, Trip

User = get_user_model()


@tag("logger", "caver", "fast")
class CaverModelTests(TestCase):
    def setUp(self):
        """Reduce log level to avoid 404 error"""
        logger = logging.getLogger("django.request")
        self.previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)

        # Test user to enable trip creation
        self.user = User.objects.create_user(
            email="test@caves.app",
            username="testuser",
            password="password",
            name="Test User",
        )
        self.user.is_active = True
        self.user.save()

        self.user2 = User.objects.create_user(
            email="test2@caves.app",
            username="testuser2",
            password="password",
            name="Test User 2",
        )
        self.user2.is_active = True
        self.user2.save()

        self.trip = Trip.objects.create(
            user=self.user,
            cave_name="Test Trip",
            start=dt.fromisoformat("2010-01-01T12:00:00+00:00"),
            end=dt.fromisoformat("2010-01-01T14:00:00+00:00"),
        )

        self.caver = Caver.objects.create(name="Test Caver", user=self.user)

        self.trip.cavers.add(self.caver)

    def test_caver_model_str(self):
        """Test that the Caver model returns the correct string representation"""
        self.assertEqual(str(self.caver), "Test Caver")

    def test_caver_model_get_absolute_url(self):
        """Test that the Caver model returns the correct absolute URL"""
        self.assertEqual(
            self.caver.get_absolute_url(), f"/log/cavers/{self.caver.uuid}/"
        )

    def test_caver_detail_view(self):
        """Test that the Caver detail view returns a 200"""
        self.client.force_login(self.user)
        response = self.client.get(self.caver.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Caver")
        self.assertContains(response, "Test Trip")
        self.assertContains(response, "Link caves.app account")

    def test_caver_detail_view_as_invalid_user(self):
        """Test that the Caver detail view returns a 403 for an invalid user"""
        self.client.force_login(self.user2)
        response = self.client.get(self.caver.get_absolute_url())
        self.assertEqual(response.status_code, 404)

    def test_caver_detail_view_as_anonymous_user(self):
        """Test that the Caver detail view returns a 403 for an anonymous user"""
        response = self.client.get(self.caver.get_absolute_url(), follow=False)
        self.assertEqual(response.status_code, 302)

    def test_caver_rename_view(self):
        """Test that the Caver rename view returns a 200"""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("log:caver_rename", args=[self.caver.uuid]),
            data={"name": "Rename Test Caver"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Rename Test Caver")

        self.caver.refresh_from_db()
        self.assertEqual(self.caver.name, "Rename Test Caver")

    def test_caver_rename_view_as_invalid_user(self):
        """Test that the Caver rename view returns a 404 for an invalid user"""
        self.client.force_login(self.user2)
        response = self.client.post(
            reverse("log:caver_rename", args=[self.caver.uuid]),
            data={"name": "Rename Test Caver"},
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.caver.name, "Test Caver")

    def test_caver_rename_view_as_anonymous_user(self):
        """Test that the Caver rename view returns a 302 for an anonymous user"""
        response = self.client.post(
            reverse("log:caver_rename", args=[self.caver.uuid]),
            data={"name": "Rename Test Caver"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.caver.name, "Test Caver")

    def test_caver_rename_view_with_invalid_data(self):
        """Test that the Caver rename view returns a 200 with invalid data"""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("log:caver_rename", args=[self.caver.uuid]),
            data={"name": "a"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter at least three characters.")
        self.assertEqual(self.caver.name, "Test Caver")

    def tearDown(self):
        """Reset the log level back to normal"""
        logger = logging.getLogger("django.request")
        logger.setLevel(self.previous_level)
