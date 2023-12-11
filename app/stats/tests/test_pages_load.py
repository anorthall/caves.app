from django.contrib.auth import get_user_model
from django.test import Client, TestCase, tag
from django.urls import reverse
from logger.factories import TripFactory

User = get_user_model()


@tag("fast", "views", "stats")
class TestStatsPagesLoad(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@caves.app",
            username="testuser",
            password="password",
            name="Test User",
        )
        self.user.is_active = True
        self.user.save()

        self.client = Client()

    def test_statistics_page_loads(self):
        """Test that the statistics page loads"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("stats:index"))
        self.assertEqual(response.status_code, 200)

    def test_statistics_page_loads_with_trips(self):
        """Test that the statistics page loads with trips"""
        self.client.force_login(self.user)
        for _ in range(250):
            TripFactory(user=self.user)
        response = self.client.get(reverse("stats:index"))
        self.assertEqual(response.status_code, 200)
