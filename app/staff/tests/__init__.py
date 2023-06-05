from django.contrib.auth import get_user_model
from django.test import Client, TestCase, tag
from django.urls import reverse

User = get_user_model()


@tag("fast", "staff", "integration")
class DashboardTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        self.user = User.objects.create_user(
            email="user@caves.app",
            username="user",
            name="Test User",
            password="password",
        )
        self.user.is_active = True
        self.user.save()

        self.staff = User.objects.create_superuser(
            email="staff@caves.app",
            username="staff",
            name="Test Staff",
            password="password",
        )
        self.staff.is_active = True
        self.staff.save()

    def test_dashboard_page_loads_as_staff(self):
        """Test that the dashboard page loads for staff"""
        self.client.force_login(self.staff)
        response = self.client.get(reverse("staff:dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_staff_index_redirect_view(self):
        """Test that the staff index redirects to the dashboard"""
        self.client.force_login(self.staff)
        response = self.client.get(reverse("staff:index"))
        self.assertRedirects(response, reverse("staff:dashboard"))

    def test_dashboard_page_returns_403_for_user(self):
        """Test that the dashboard page returns 403 for a user"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("staff:dashboard"))
        self.assertEqual(response.status_code, 403)
