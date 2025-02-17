from django.contrib.auth import get_user_model
from django.test import TestCase, tag
from django.urls import reverse
from django.utils import timezone

from ..models import FAQ, News

User = get_user_model()


@tag("fast")
class TestNewsAndFAQsModels(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            email="user@caves.app",
            username="user",
            password="password",
            name="User",
        )
        self.user.is_active = True
        self.user.save()

        self.news = News.objects.create(
            title="Test News",
            slug="test-news",
            posted_at=timezone.now(),
            author=self.user,
            content="Test content",
            is_published=True,
        )

        self.faq = FAQ.objects.create(
            question="Test Question",
            answer="Test Answer",
            author=self.user,
        )

    @tag("news")
    def test_news_str(self):
        """Test the news model string representation."""
        self.assertEqual(str(self.news), self.news.title)

    @tag("help", "faqs")
    def test_faq_str(self):
        """Test the FAQ model string representation."""
        self.assertEqual(str(self.faq), self.faq.question)

    @tag("news")
    def test_news_get_absolute_url(self):
        """Test the news model get_absolute_url method."""
        self.assertEqual(self.news.get_absolute_url(), "/news/test-news/")

    @tag("news", "admin", "views")
    def test_news_author_autoassign(self):
        """Test that the news author is autoassigned in Django admin."""
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

    @tag("help", "faqs", "admin", "views")
    def test_faq_author_autoassign(self):
        """Test that the FAQ author is autoassigned in Django admin."""
        self.client.force_login(self.user)
        self.client.post(
            reverse("admin:core_faq_add"),
            {
                "question": "Test Autoassign",
                "answer": "Test answer",
                "posted_at_0": timezone.now().date(),
                "posted_at_1": timezone.now().time(),
            },
        )

        faq = FAQ.objects.get(question="Test Autoassign")
        self.assertEqual(faq.author, self.user)
