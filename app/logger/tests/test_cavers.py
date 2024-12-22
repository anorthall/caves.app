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
        """Reduce log level to avoid 404 error."""
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

        self.trip2 = Trip.objects.create(
            user=self.user,
            cave_name="Test Trip 2",
            start=dt.fromisoformat("2010-01-01T12:00:00+00:00"),
            end=dt.fromisoformat("2010-01-01T14:00:00+00:00"),
        )

        self.caver = Caver.objects.create(name="Test Caver", user=self.user)
        self.caver2 = Caver.objects.create(name="Test Caver 2", user=self.user)

        self.trip.cavers.add(self.caver)
        self.trip2.cavers.add(self.caver2)

    def test_caver_model_str(self):
        """Test that the Caver model returns the correct string representation."""
        self.assertEqual(str(self.caver), "Test Caver")

    def test_caver_model_get_absolute_url(self):
        """Test that the Caver model returns the correct absolute URL."""
        self.assertEqual(self.caver.get_absolute_url(), f"/log/cavers/{self.caver.uuid}/")

    def test_caver_detail_view(self):
        """Test that the Caver detail view returns a 200."""
        self.client.force_login(self.user)
        response = self.client.get(self.caver.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Caver")
        self.assertContains(response, "Test Trip")
        self.assertContains(response, "Link caves.app account")

    @tag("privacy")
    def test_caver_detail_view_as_invalid_user(self):
        """Test that the Caver detail view returns a 403 for an invalid user."""
        self.client.force_login(self.user2)
        response = self.client.get(self.caver.get_absolute_url())
        self.assertEqual(response.status_code, 404)

    @tag("privacy")
    def test_caver_detail_view_as_anonymous_user(self):
        """Test that the Caver detail view returns a 403 for an anonymous user."""
        response = self.client.get(self.caver.get_absolute_url(), follow=False)
        self.assertEqual(response.status_code, 302)

    def test_caver_rename_view(self):
        """Test that the Caver rename view returns a 200."""
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

    @tag("privacy")
    def test_caver_rename_view_as_invalid_user(self):
        """Test that the Caver rename view returns a 404 for an invalid user."""
        self.client.force_login(self.user2)
        response = self.client.post(
            reverse("log:caver_rename", args=[self.caver.uuid]),
            data={"name": "Rename Test Caver"},
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.caver.name, "Test Caver")

    @tag("privacy")
    def test_caver_rename_view_as_anonymous_user(self):
        """Test that the Caver rename view returns a 302 for an anonymous user."""
        response = self.client.post(
            reverse("log:caver_rename", args=[self.caver.uuid]),
            data={"name": "Rename Test Caver"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.caver.name, "Test Caver")

    def test_caver_rename_view_with_invalid_data(self):
        """Test that the Caver rename view returns a 200 with invalid data."""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("log:caver_rename", args=[self.caver.uuid]),
            data={"name": "a"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter at least three characters.")
        self.assertEqual(self.caver.name, "Test Caver")

    def test_caver_merge_view(self):
        """Test that the Caver merge view returns a 200."""
        self.client.force_login(self.user)
        self.assertEqual(self.caver.trip_set.count(), 1)
        self.assertEqual(self.caver2.trip_set.count(), 1)

        response = self.client.post(
            reverse("log:caver_merge", args=[self.caver.uuid]),
            data={"caver": self.caver2.uuid},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.caver.refresh_from_db()
        self.assertEqual(self.caver.trip_set.count(), 2)
        self.assertEqual(self.caver.name, "Test Caver")

        with self.assertRaises(Caver.DoesNotExist):
            self.caver2.refresh_from_db()

    @tag("privacy")
    def test_caver_merge_view_as_invalid_user(self):
        """Test that the Caver merge view returns a 404 for an invalid user."""
        self.client.force_login(self.user2)
        response = self.client.post(
            reverse("log:caver_merge", args=[self.caver.uuid]),
            data={"caver": self.caver2.uuid},
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.caver.name, "Test Caver")
        self.assertEqual(self.caver2.name, "Test Caver 2")

    @tag("privacy")
    def test_caver_merge_view_as_anonymous_user(self):
        """Test that the Caver merge view returns a 302 for an anonymous user."""
        response = self.client.post(
            reverse("log:caver_merge", args=[self.caver.uuid]),
            data={"caver": self.caver2.uuid},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.caver.name, "Test Caver")
        self.assertEqual(self.caver2.name, "Test Caver 2")

    def test_caver_merge_view_with_invalid_data(self):
        """Test that the Caver merge view does not merge with invalid data."""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("log:caver_merge", args=[self.caver.uuid]),
            data={"caver": "invalid-uuid"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Select a valid choice.")
        self.assertEqual(self.caver.name, "Test Caver")
        self.assertEqual(self.caver2.name, "Test Caver 2")

    def test_caver_link_and_unlink_views(self):
        """Test that the Caver link and unlink views."""
        self.client.force_login(self.user)
        self.assertEqual(self.caver.linked_account, None)

        self.user.friends.add(self.user2)
        self.user2.friends.add(self.user)

        response = self.client.post(
            reverse("log:caver_link", args=[self.caver.uuid]),
            data={"account": self.user2.username},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.caver.refresh_from_db()
        self.assertEqual(self.caver.linked_account, self.user2)

        response = self.client.post(
            reverse("log:caver_unlink", args=[self.caver.uuid]),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.caver.refresh_from_db()
        self.assertEqual(self.caver.linked_account, None)

    @tag("privacy")
    def test_caver_link_and_unlink_views_as_invalid_user(self):
        """Test that the Caver link and unlink views return a 404 for an invalid user."""
        self.client.force_login(self.user2)
        response = self.client.post(
            reverse("log:caver_link", args=[self.caver.uuid]),
            data={"account": self.user2.username},
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.caver.linked_account, None)

        response = self.client.post(
            reverse("log:caver_unlink", args=[self.caver.uuid]),
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.caver.linked_account, None)

    def test_caver_link_message_appears_on_caver_detail_view(self):
        """Test that the Caver link message appears on the Caver detail view."""
        self.client.force_login(self.user)
        self.assertEqual(self.caver.linked_account, None)

        self.user.friends.add(self.user2)
        self.user2.friends.add(self.user)

        response = self.client.get(self.caver.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "This caver record is linked to the caves.app account of")

        response = self.client.post(
            reverse("log:caver_link", args=[self.caver.uuid]),
            data={"account": self.user2.username},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "The caver record for Test Caver has been linked to @testuser2."
        )
        self.caver.refresh_from_db()
        self.assertEqual(self.caver.linked_account, self.user2)

        response = self.client.get(self.caver.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user2.get_absolute_url())
        self.assertContains(response, "This caver record is linked to the caves.app account of")

    def tearDown(self):
        """Reset the log level back to normal."""
        logger = logging.getLogger("django.request")
        logger.setLevel(self.previous_level)
