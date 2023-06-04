from django.contrib.auth import get_user_model
from django.test import Client, TestCase, tag
from django.urls import reverse
from django.utils import timezone

from ..models import FAQ, News

User = get_user_model()


@tag("integration", "admin", "fast")
class TestAuthorAutoassignForNewsAndFAQs(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="superuser@caves.app",
            username="superuser",
            password="password",
            name="Super User",
        )
        self.user.is_superuser = True
        self.user.is_active = True
        self.user.save()

        self.client = Client()

    def test_news_author_autoassign(self):
        """Test that the news author is autoassigned in Django admin"""
        self.client.force_login(self.user)
        self.client.post(
            reverse("admin:core_news_add"),
            {
                "title": "Test News",
                "slug": "test-news",
                "content": "Test content",
                "posted_at_0": timezone.now().date(),
                "posted_at_1": timezone.now().time(),
            },
        )

        news = News.objects.get(title="Test News")
        self.assertEqual(news.author, self.user)

    def test_faq_author_autoassign(self):
        """Test that the FAQ author is autoassigned in Django admin"""
        self.client.force_login(self.user)
        self.client.post(
            reverse("admin:core_faq_add"),
            {
                "question": "Test Question",
                "answer": "Test answer",
                "posted_at_0": timezone.now().date(),
                "posted_at_1": timezone.now().time(),
            },
        )

        faq = FAQ.objects.get(question="Test Question")
        self.assertEqual(faq.author, self.user)
