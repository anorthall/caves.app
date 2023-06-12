from unittest import skipIf
from unittest.mock import MagicMock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.fields.files import ImageFieldFile
from django.test import Client, TestCase, tag
from django.urls import reverse
from django.utils import timezone

from ..models import Trip, TripPhoto, trip_photo_upload_path

User = get_user_model()


def aws_not_configured():
    """Return True if AWS is not configured"""
    return (
        not settings.AWS_S3_ACCESS_KEY_ID
        or not settings.AWS_S3_SECRET_ACCESS_KEY
        or not settings.AWS_STORAGE_BUCKET_NAME
    )


@tag("logger", "tripphotos", "fast")
class TripPhotoTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.user = User.objects.create_user(
            email="test@users.app",
            name="Test User",
            username="testuser",
            password="password",
        )
        self.user.is_active = True
        self.user.save()

        self.user2 = User.objects.create_user(
            email="test2@users.app",
            name="Test User 2",
            username="testuser2",
            password="password",
        )
        self.user2.is_active = True
        self.user2.save()

        self.trip = Trip.objects.create(
            user=self.user,
            cave_name="Test Cave",
            start=timezone.now(),
        )

        self.photo = TripPhoto.objects.create(
            trip=self.trip, user=self.user, photo=None
        )
        self.photo.photo = ImageFieldFile(
            self.photo, self.photo.photo.field, "test-file.jpg"
        )
        self.photo.is_valid = True
        self.photo.save()

    def test_trip_photo_upload_path(self):
        """Test that the upload path is correct"""
        instance = MagicMock()
        instance.user = self.user
        instance.trip = self.trip
        instance.uuid = "12345678-1234-5678-1234-567812345678"
        filename = "test-file.jpg"

        expected = f"p/{instance.user.uuid}/{instance.trip.uuid}/{instance.uuid}.jpg"
        actual = trip_photo_upload_path(instance, filename)
        self.assertEqual(expected, actual)

    def test_trip_photo_page_loads(self):
        """Test that the trip photo page loads"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("log:trip_photos", args=[self.trip.uuid]))
        self.assertEqual(response.status_code, 200)

    @skipIf(aws_not_configured(), "AWS is not configured")
    @tag("privacy")
    def test_trip_photo_page_does_not_load_for_other_users(self):
        """Test that the trip photo page does not load for other users"""
        self.client.force_login(self.user2)
        response = self.client.get(reverse("log:trip_photos", args=[self.trip.uuid]))
        self.assertEqual(response.status_code, 403)

    @tag("privacy")
    def test_trip_photo_page_does_not_load_for_anonymous_users(self):
        """Test that the trip photo page does not load for anonymous users"""
        response = self.client.get(reverse("log:trip_photos", args=[self.trip.uuid]))
        self.assertEqual(response.status_code, 403)

    @tag("privacy")
    @skipIf(aws_not_configured(), "AWS is not configured")
    def test_trip_photo_privacy(self):
        """Test that photos do not show for other users when private"""
        self.trip.privacy = Trip.PUBLIC
        self.trip.private_photos = True
        self.trip.save()

        # Test that another user cannot see the photo whilst it is private
        self.client.force_login(self.user2)
        response = self.client.get(self.trip.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "test-file.jpg")

        # Test that the owner can see the photo whilst it is private
        self.client.force_login(self.user)
        response = self.client.get(self.trip.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "test-file.jpg")

        # Set the photo to public
        self.trip.private_photos = False
        self.trip.save()

        # Test that another user can see the photo whilst it is public
        self.client.force_login(self.user2)
        response = self.client.get(self.trip.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "test-file.jpg")

        # Test that the owner can see the photo whilst it is public
        self.client.force_login(self.user)
        response = self.client.get(self.trip.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "test-file.jpg")

    @skipIf(aws_not_configured(), "AWS is not configured")
    def test_trip_photo_update_privacy(self):
        """Test updating the privacy of photos for a trip"""
        self.trip.private_photos = False
        self.trip.save()

        self.client.force_login(self.user)
        response = self.client.post(
            reverse("log:trip_photos", args=[self.trip.uuid]),
            {
                "private_photos": True,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "The photo privacy setting for this trip has been updated."
        )

        self.trip.refresh_from_db()
        self.assertTrue(self.trip.private_photos)

    @tag("privacy")
    def test_trip_photo_update_privacy_as_other_user(self):
        """Test updating the privacy of photos for a trip as another user"""
        self.trip.private_photos = False
        self.trip.save()

        self.client.force_login(self.user2)
        response = self.client.post(
            reverse("log:trip_photos", args=[self.trip.uuid]),
            {
                "private_photos": True,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 403)

        self.trip.refresh_from_db()
        self.assertFalse(self.trip.private_photos)

    def test_trip_photo_delete(self):
        """Test deleting a photo"""
        uuid = self.photo.uuid

        self.client.force_login(self.user)
        response = self.client.post(
            reverse("log:trip_photos_delete"),
            {
                "photoUUID": uuid,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The photo has been deleted.")

        qs = TripPhoto.objects.filter(uuid=uuid)
        self.assertEqual(qs.count(), 0)

    @tag("privacy")
    def test_trip_photo_delete_as_other_user(self):
        """Test deleting a photo as another user"""
        uuid = self.photo.uuid

        self.client.force_login(self.user2)
        response = self.client.post(
            reverse("log:trip_photos_delete"),
            {
                "photoUUID": uuid,
            },
        )
        self.assertEqual(response.status_code, 403)

        qs = TripPhoto.objects.filter(uuid=uuid)
        self.assertEqual(qs.count(), 1)

    def test_trip_photo_delete_invalid_uuid(self):
        """Test deleting a photo with an invalid UUID"""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("log:trip_photos_delete"),
            {
                "photoUUID": "12345678-1234-5678-1234-567812345678",
            },
        )
        self.assertEqual(response.status_code, 404)

    @skipIf(aws_not_configured(), "AWS is not configured")
    def test_trip_photo_update_caption(self):
        """Test updating the caption of a photo"""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("log:trip_photos_update"),
            {
                "photoUUID": self.photo.uuid,
                "caption": "New caption",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The photo has been updated.")

        self.photo.refresh_from_db()
        self.assertEqual(self.photo.caption, "New caption")

    @skipIf(aws_not_configured(), "AWS is not configured")
    def test_trip_photo_update_caption_with_a_caption_that_is_too_long(self):
        """Test updating the caption of a photo with a caption that is too long"""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("log:trip_photos_update"),
            {
                "photoUUID": self.photo.uuid,
                "caption": "A" * 256,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The photo could not be updated.")

        self.photo.refresh_from_db()
        self.assertEqual(self.photo.caption, "")

    @tag("privacy")
    def test_trip_photo_update_caption_as_other_user(self):
        """Test updating the caption of a photo as another user"""
        self.client.force_login(self.user2)
        response = self.client.post(
            reverse("log:trip_photos_update"),
            {
                "photoUUID": self.photo.uuid,
                "caption": "New caption",
            },
        )
        self.assertEqual(response.status_code, 403)

        self.photo.refresh_from_db()
        self.assertEqual(self.photo.caption, "")

    def test_trip_photo_delete_all(self):
        """Test deleting all photos"""
        TripPhoto.objects.filter(trip=self.trip).delete()

        for i in range(10):
            photo = TripPhoto.objects.create(trip=self.trip, user=self.user, photo=None)
            photo.photo = ImageFieldFile(
                self.photo, self.photo.photo.field, f"test-file-{i}.jpg"
            )
            photo.is_valid = True
            photo.save()
        self.assertEqual(TripPhoto.objects.filter(trip=self.trip).count(), 10)

        self.client.force_login(self.user)
        response = self.client.post(
            reverse("log:trip_photos_delete_all", args=[self.trip.uuid]), follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "All photos for the trip have been deleted.")

        qs = TripPhoto.objects.filter(trip=self.trip)
        self.assertEqual(qs.count(), 0)

    @tag("privacy")
    def test_trip_photo_delete_all_as_other_user(self):
        """Test deleting all photos as another user"""
        self.assertEqual(TripPhoto.objects.filter(trip=self.trip).count(), 1)
        self.client.force_login(self.user2)
        response = self.client.post(
            reverse("log:trip_photos_delete_all", args=[self.trip.uuid]),
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(TripPhoto.objects.filter(trip=self.trip).count(), 1)

    def test_trip_photo_str_method(self):
        """Test the string representation of a trip photo"""
        self.assertEqual(str(self.photo), f"Photo for {self.trip} by {self.trip.user}")

    @skipIf(aws_not_configured(), "AWS is not configured")
    def test_trip_photo_get_absolute_url(self):
        """Test the get_absolute_url method"""
        self.assertEqual(self.photo.get_absolute_url(), self.photo.url)

    @skipIf(aws_not_configured(), "AWS is not configured")
    def test_invalid_photos_do_not_show_on_trip_detail_page(self):
        """Test that invalid photos do not show on the trip detail page"""
        self.assertEqual(self.photo.is_valid, True)

        self.client.force_login(self.user)
        response = self.client.get(self.trip.get_absolute_url())
        self.assertContains(response, "test-file.jpg")

        self.photo.is_valid = False
        self.photo.save()

        response = self.client.get(self.trip.get_absolute_url())
        self.assertNotContains(response, "test-file.jpg")
