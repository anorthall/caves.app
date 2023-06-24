from django.test import TestCase, tag
from django.urls import reverse
from users.models import CavingUser as User


@tag("fast", "import")
class ImportTests(TestCase):
    def setUp(self):
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
