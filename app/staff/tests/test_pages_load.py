from django.contrib.auth import get_user_model
from django.test import Client, TestCase, tag
from django.urls import reverse

User = get_user_model()


@tag("fast", "views", "staff")
class TestStaffPagesLoad(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@caves.app",
            username="testuser",
            password="password",
            name="Test User",
        )
        self.user.is_active = True
        self.user.save()

        self.superuser = User.objects.create_superuser(
            email="superuser@caves.app",
            username="superuser",
            password="password",
            name="Test User",
        )
        self.user.is_active = True
        self.user.save()

        self.client = Client()

    @tag("privacy")
    def test_dashboard_returns_403_as_non_superuser(self):
        """Test that the dashboard page returns 403 as a non superuser."""
        self.client.force_login(self.user)
        response = self.client.get(reverse("staff:dashboard"))
        self.assertEqual(response.status_code, 403)

    @tag("privacy")
    def test_staff_index_page_returns_403_as_non_superuser(self):
        """Test that the staff:index view returns 403 as a non superuser."""
        self.client.force_login(self.user)
        response = self.client.get(reverse("staff:index"))
        self.assertEqual(response.status_code, 403)

    def test_dashboard_loads_as_superuser(self):
        """Test that the dashboard page loads as a superuser."""
        self.client.force_login(self.superuser)
        response = self.client.get(reverse("staff:dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_loads_as_moderator(self):
        """Test that the dashboard page loads as a moderator."""
        self.client.force_login(self.superuser)
        self.superuser.has_mod_perms = True
        self.superuser.is_superuser = False
        self.superuser.save()

        response = self.client.get(reverse("staff:dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_staff_index_page_redirect_view(self):
        """Test that the staff:index view redirects to the dashboard."""
        self.client.force_login(self.superuser)
        response = self.client.get(reverse("staff:index"))
        self.assertRedirects(response, reverse("staff:dashboard"))
