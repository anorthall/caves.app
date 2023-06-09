from django.contrib.auth import get_user_model
from django.test import Client, TestCase, tag
from django.urls import reverse
from django.utils import timezone

from ..models import News

User = get_user_model()


@tag("fast", "views", "core")
class TestCorePagesLoad(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@caves.app",
            username="testuser",
            password="password",
            name="Test User",
        )

        self.news1 = News.objects.create(
            title="Test News 1",
            slug="test-news-1",
            posted_at=timezone.now(),
            author=self.user,
            content="Test News 1 Content",
            is_published=True,
        )

        self.news2 = News.objects.create(
            title="Test News 2",
            slug="test-news-2",
            posted_at=timezone.now(),
            author=self.user,
            content="Test News 2 Content",
            is_published=True,
        )

        self.client = Client()

    def test_news_page_loads(self):
        """Test that the news page loads"""
        response = self.client.get(reverse("core:news"))
        self.assertEqual(response.status_code, 200)

    def test_news_detail_page_loads(self):
        """Test that the news detail page loads"""
        response = self.client.get(reverse("core:news_detail", args=[self.news1.slug]))
        self.assertEqual(response.status_code, 200)

    def test_help_page_loads(self):
        """Test that the help page loads"""
        response = self.client.get(reverse("core:help"))
        self.assertEqual(response.status_code, 200)
