from django.contrib import auth
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, tag
from django.urls import reverse
from users.models import Notification

User = get_user_model()


@tag("integration", "fast", "admin")
class AdminToolsIntegrationTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@admin.app",
            username="admin",
            password="admin",
            name="admin",
        )
        self.admin.is_active = True
        self.admin.is_superuser = True
        self.admin.save()

        self.user = User.objects.create_user(
            email="user@user.app",
            username="user",
            password="user",
            name="user",
        )
        self.user.is_active = True
        self.user.save()

        self.client = Client()

    def test_admin_tools_login_as_form(self):
        """Test the login as form"""
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("log:admin_tools"),
            {
                "login_as": self.user.email,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        user = auth.get_user(self.client)
        self.assertEqual(user, self.user)
        self.assertContains(response, f"Now logged in as {self.user.email}")

    def test_admin_tools_login_as_form_with_a_superuser_account(self):
        """Test the login as form with a superuser account"""
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("log:admin_tools"),
            {
                "login_as": self.admin.email,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cannot login as a superuser via this page")

    def test_admin_tools_notify_all_users_form(self):
        """Test the notify all users form"""
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("log:admin_tools"),
            {
                "notify": "notify",
                "message": "Test message",
                "url": "https://caves.app/",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Notifications sent.")

        self.assertEqual(Notification.objects.count(), 2)
        for notification in Notification.objects.all():
            self.assertEqual(notification.message, "Test message")
            self.assertEqual(notification.url, "https://caves.app/")
