from django.contrib.auth import get_user_model
from django.test import TestCase, tag
from django.utils import timezone
from logger.models import Trip

from ..models import Comment

User = get_user_model()


@tag("comments", "fast")
class TestCommentModel(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@test.app",
            username="testuser",
            password="password",
            name="Test User",
        )
        self.user.is_active = True
        self.user.save()

        self.trip = Trip.objects.create(
            user=self.user,
            cave_name="Test Cave",
            start=timezone.now(),
        )

    def test_comment_str(self):
        """Test the Comment model __str__ function"""
        c = Comment.objects.create(
            author=self.user, trip=self.trip, content="This is a comment"
        )
        self.assertEqual(str(c), f"Comment by {c.author} on {c.trip}")
