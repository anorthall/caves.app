from django.test import Client, TestCase, tag
from django.urls import reverse

from ..factories import UserFactory
from ..models import Notification


@tag("fast", "users", "notifications", "views")
class NotificationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = UserFactory(is_active=True)

        for i in range(20):
            self.user.notify(f"Test {i}a", "/")

    def test_notifications_are_displayed(self):
        """Test notifications are displayed on the user's profile."""
        self.client.force_login(self.user)

        response = self.client.get(reverse("users:account_detail"))
        for i in range(1, 11):
            self.assertNotContains(response, f"Test {i}a")

        for i in range(11, 20):
            self.assertContains(response, f"Test {i}a")

    def test_notification_redirect_view(self):
        """Test the notification redirect view."""
        self.client.force_login(self.user)
        pk = self.user.notify("Test", "/test/").pk
        response = self.client.get(reverse("users:notification", args=[pk]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/test/")

    def test_notification_list_view(self):
        """Test the notification list view."""
        self.client.force_login(self.user)
        response = self.client.get(reverse("users:notifications"))
        self.assertEqual(response.status_code, 200)
        for i in range(11, 20):
            self.assertContains(response, f"Test {i}")

    def test_mark_all_notifications_as_read_view(self):
        """Test the mark all notifications as read view."""
        for n in Notification.objects.filter(user=self.user):
            self.assertEqual(n.read, False)

        self.client.force_login(self.user)
        response = self.client.get(reverse("users:notifications_mark_read"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("users:notifications"))

        for n in Notification.objects.filter(user=self.user):
            self.assertEqual(n.read, True)
