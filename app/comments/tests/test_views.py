import uuid

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, tag
from django.urls import reverse
from django.utils import timezone
from logger.models import Trip
from users.models import Notification

from ..models import Comment

User = get_user_model()


@tag("fast", "comments", "views")
class TestCommentViews(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@test.app",
            username="testuser",
            password="password",
            name="Test User",
        )
        self.user.is_active = True
        self.user.save()

        self.user2 = User.objects.create_user(
            email="user2@test.app",
            username="testuser2",
            password="password",
            name="Test User 2",
        )
        self.user2.is_active = True
        self.user2.save()

        self.trip = Trip.objects.create(
            user=self.user,
            cave_name="Test Cave",
            start=timezone.now(),
        )

        self.client.force_login(self.user)

    def test_comments_appear_on_trip_detail_page(self):
        """Test that comments appear on the trip detail page"""
        comment = Comment.objects.create(
            author=self.user,
            trip=self.trip,
            content="Test comment 123456",
        )
        response = self.client.get(reverse("log:trip_detail", args=[self.trip.uuid]))
        self.assertContains(response, comment.content)

    def test_comments_do_not_appear_on_trip_detail_page_when_disabled(self):
        """Test that comments do not appear on the trip detail page when disabled"""
        self.user.allow_comments = False
        self.user.save()

        comment = Comment.objects.create(
            author=self.user,
            trip=self.trip,
            content="Test comment 123456",
        )
        response = self.client.get(reverse("log:trip_detail", args=[self.trip.uuid]))
        self.assertNotContains(response, comment.content)

    def test_add_comment_via_post_request(self):
        """Test that a comment can be added via a POST request"""
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("comments:add", args=[self.trip.uuid]),
            {
                "content": "Test comment 123456",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.count(), 1)
        self.assertContains(response, "Test comment")

    def test_add_comment_via_post_request_to_object_the_user_cannot_view(self):
        """Test that a comment cannot be added to an object the user cannot view"""
        self.client.force_login(self.user2)
        self.trip.privacy = Trip.PRIVATE
        self.trip.save()

        response = self.client.post(
            reverse("comments:add", args=[self.trip.uuid]),
            {
                "content": "Test comment",
            },
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Comment.objects.count(), 0)

    def test_add_comment_via_post_request_when_not_logged_in(self):
        """Test that the comment view does not load when not logged in"""
        self.client.logout()
        response = self.client.post(
            reverse("comments:add", args=[self.trip.uuid]),
            {
                "content": "Test comment",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Comment.objects.count(), 0)

    def test_delete_comment(self):
        """Test that a comment can be deleted"""
        comment = Comment.objects.create(
            author=self.user,
            trip=self.trip,
            content="Test comment",
        )

        self.client.force_login(self.user)
        response = self.client.post(
            reverse("comments:delete", args=[comment.uuid]),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The comment has been deleted")
        self.assertEqual(Comment.objects.count(), 0)

    def test_delete_comment_that_does_not_belong_to_the_user(self):
        """Test that a comment cannot be deleted if it does not belong to the user"""
        comment = Comment.objects.create(
            author=self.user,
            trip=self.trip,
            content="Test comment",
        )

        self.client.force_login(self.user2)
        response = self.client.post(
            reverse("comments:delete", args=[comment.uuid]),
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Comment.objects.count(), 1)

    def test_htmx_comment_view_on_an_object_the_user_cannot_view(self):
        """Test that the HTMX comment view respects privacy"""
        self.client.force_login(self.user2)

        self.trip.privacy = Trip.PRIVATE
        self.trip.save()

        response = self.client.get(
            reverse("comments:htmx_comments", args=[self.trip.uuid]),
        )
        self.assertEqual(response.status_code, 403)

    def test_comments_send_a_notification_when_posted(self):
        """Test that a notification is sent when a comment is posted"""
        self.client.force_login(self.user2)
        self.trip.privacy = Trip.PUBLIC
        self.trip.save()

        response = self.client.post(
            reverse("comments:add", args=[self.trip.uuid]),
            {
                "content": "Test comment",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

        self.client.force_login(self.user)
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(Notification.objects.first().user, self.user)
        self.assertEqual(Notification.objects.first().url, self.trip.get_absolute_url())

        response = self.client.get(reverse("log:index"))
        self.assertContains(response, f"{self.user2} commented on your trip")

    def test_adding_comment_with_too_much_content(self):
        """Test that a comment cannot be added with too much content"""
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("comments:add", args=[self.trip.uuid]),
            {
                "content": "x" * 4000,
            },
            follow=True,
        )
        self.assertContains(
            response,
            "Your comment must be less than 2000 characters long.",
        )
        self.assertEqual(Comment.objects.count(), 0)

    def test_adding_comment_on_an_object_that_does_not_exist(self):
        """Test that a comment cannot be added to an object that does not exist"""
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("comments:add", args=[uuid.uuid4()]),
            {
                "content": "Test comment",
            },
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Comment.objects.count(), 0)

    def test_adding_comment_on_an_object_where_the_user_disallows_comments(self):
        """Test users cannot comment where the user disallows comments"""
        self.user.allow_comments = False
        self.user.save()

        self.trip.privacy = Trip.PUBLIC
        self.trip.save()

        self.client.force_login(self.user2)

        response = self.client.post(
            reverse("comments:add", args=[self.trip.uuid]),
            {
                "content": "Test comment",
            },
            follow=True,
        )
        self.assertContains(
            response,
            "There was an error adding your comment. Please try again.",
        )
        self.assertEqual(Comment.objects.count(), 0)

    def test_comments_send_an_email_when_enabled(self):
        """Test that a comment sends an email when enabled"""
        self.user.email_comments = True
        self.user.save()

        self.trip.privacy = Trip.PUBLIC
        self.trip.save()

        self.client.force_login(self.user2)
        self.client.post(
            reverse("comments:add", args=[self.trip.uuid]),
            {
                "content": "Test comment",
            },
            follow=True,
        )

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            f"{self.user2} commented on your trip to {self.trip.cave_name}",
        )

    def test_comments_do_not_send_an_email_when_disabled(self):
        """Test that a comment does not send an email when disabled"""
        self.user.email_comments = False
        self.user.save()

        self.trip.privacy = Trip.PUBLIC
        self.trip.save()

        self.client.force_login(self.user2)
        self.client.post(
            reverse("comments:add", args=[self.trip.uuid]),
            {
                "content": "Test comment",
            },
            follow=True,
        )

        self.assertEqual(len(mail.outbox), 0)
