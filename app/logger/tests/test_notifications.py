from django.test import Client, TestCase, tag
from django.urls import reverse
from users.models import CavingUser

User = CavingUser


# TODO: Move to Users app?
@tag("users", "notifications", "fast")
class NotificationTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.user = User.objects.create_user(
            email="user@caves.app",
            username="user",
            password="password",
            name="User Name",
        )
        self.user.is_active = True
        self.user.save()

        self.user2 = User.objects.create_user(
            email="user2@caves.app",
            username="user2",
            password="password",
            name="User 2 Name",
        )
        self.user2.is_active = True
        self.user2.save()

    @tag("privacy")
    def test_notification_redirect_view_as_invalid_user(self):
        """Test that the notification redirect view returns a 403 for an invalid user"""
        self.client.force_login(self.user2)
        notification = self.user.notify("Test notification", "/")
        response = self.client.get(
            reverse("users:notification", args=[notification.pk]),
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(notification.read, False)
