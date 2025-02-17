from django.contrib.auth import get_user_model
from django.core import mail
from django.test import Client, TestCase, tag
from django.urls import reverse

from users.models import FriendRequest

User = get_user_model()


@tag("unit", "users", "fast")
class SocialUnitTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.user = User.objects.create_user(
            email="test@user.app",
            username="test",
            password="password",
            name="test",
        )

        self.user2 = User.objects.create_user(
            email="test2@user.app",
            username="test2",
            password="password",
            name="test2",
        )

    def test_friend_request_str(self):
        """Test the __str__ method of the FriendRequest model."""
        request = FriendRequest.objects.create(
            user_from=self.user,
            user_to=self.user2,
        )
        self.assertEqual(str(request), f"{self.user} -> {self.user2}")

    def test_notification_str(self):
        """Test the __str__ method of the Notification model."""
        msg = "Notification message"
        notification = self.user.notify(msg, "/")
        self.assertEqual(str(notification), msg)


@tag("integration", "fast", "users")
class SocialIntegrationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@caves.app",
            username="user",
            password="password",
            name="user",
        )
        self.user.is_active = True
        self.user.save()

        self.user2 = User.objects.create_user(
            email="user2@caves.app",
            username="user2",
            password="password",
            name="user2",
        )
        self.user2.is_active = True
        self.user2.save()

        self.user3 = User.objects.create_user(
            email="user3@caves.app",
            username="user3",
            password="password",
            name="user3",
        )
        self.user3.is_active = True
        self.user3.save()

    def test_sending_a_friend_request_by_username(self):
        """Test sending a friend request by username."""
        self.client.force_login(self.user)
        self.client.post(reverse("users:friend_add"), {"user": self.user2.username})
        self.assertEqual(FriendRequest.objects.count(), 1)
        self.assertEqual(len(self.user2.notifications.all()), 1)
        self.assertEqual(FriendRequest.objects.first().user_from, self.user)
        self.assertEqual(FriendRequest.objects.first().user_to, self.user2)

    def test_sending_a_friend_request_by_email(self):
        """Test sending a friend request by email."""
        self.client.force_login(self.user)
        self.user2.allow_friend_email = True
        self.user2.save()
        self.client.post(reverse("users:friend_add"), {"user": self.user2.email})
        self.assertEqual(FriendRequest.objects.count(), 1)
        self.assertEqual(len(self.user2.notifications.all()), 1)
        self.assertEqual(FriendRequest.objects.first().user_from, self.user)
        self.assertEqual(FriendRequest.objects.first().user_to, self.user2)

    def test_friend_request_emails_are_sent_when_enabled(self):
        """Test friend request emails are sent when enabled."""
        self.client.force_login(self.user)
        self.user2.allow_friend_email = True
        self.user2.email_friend_requests = True
        self.user2.save()

        self.user.email_friend_requests = True
        self.user.save()

        self.assertEqual(len(mail.outbox), 0)

        # Send a friend request
        self.client.post(reverse("users:friend_add"), {"user": self.user2.email})
        self.assertEqual(FriendRequest.objects.count(), 1)
        self.assertEqual(len(self.user2.notifications.all()), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f"{self.user.name} sent you a friend request")
        self.assertEqual(FriendRequest.objects.first().user_from, self.user)
        self.assertEqual(FriendRequest.objects.first().user_to, self.user2)

        # Now accept the friend request
        self.client.force_login(self.user2)
        self.client.post(
            reverse("users:friend_request_accept", args=[FriendRequest.objects.first().pk])
        )
        self.assertIn(self.user2, self.user.friends.all())
        self.assertIn(self.user, self.user2.friends.all())
        self.assertEqual(len(self.user.notifications.all()), 1)
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(FriendRequest.objects.count(), 0)
        self.assertEqual(mail.outbox[1].subject, f"{self.user2.name} accepted your friend request")

    def test_friend_request_emails_are_not_sent_when_disabled(self):
        """Test friend request emails are not sent when disabled."""
        self.client.force_login(self.user)
        self.user2.allow_friend_email = True
        self.user2.email_friend_requests = False
        self.user2.save()

        self.user.email_friend_requests = False
        self.user.save()

        self.assertEqual(len(mail.outbox), 0)

        # Send a friend request
        self.client.post(reverse("users:friend_add"), {"user": self.user2.email})
        self.assertEqual(FriendRequest.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(FriendRequest.objects.first().user_from, self.user)
        self.assertEqual(FriendRequest.objects.first().user_to, self.user2)

        # Now accept the friend request
        self.client.force_login(self.user2)
        self.client.post(
            reverse("users:friend_request_accept", args=[FriendRequest.objects.first().pk])
        )
        self.assertIn(self.user2, self.user.friends.all())
        self.assertIn(self.user, self.user2.friends.all())
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(FriendRequest.objects.count(), 0)

    def test_friend_request_disallowed_by_email(self):
        """Test sending a friend request by email is disallowed."""
        self.client.force_login(self.user)
        self.user2.allow_friend_email = False
        self.user2.save()
        self.client.post(reverse("users:friend_add"), {"user": self.user2.email})
        self.assertEqual(FriendRequest.objects.count(), 0)

    def test_friend_request_disallowed_by_username(self):
        """Test sending a friend request by username is disallowed."""
        self.client.force_login(self.user)
        self.user2.allow_friend_username = False
        self.user2.save()
        self.client.post(reverse("users:friend_add"), {"user": self.user2.username})
        self.assertEqual(FriendRequest.objects.count(), 0)

    def test_adding_self_as_friend_is_not_permitted(self):
        """Test adding self as a friend is not permitted."""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("users:friend_add"), {"user": self.user.username}, follow=True
        )
        self.assertEqual(FriendRequest.objects.count(), 0)
        self.assertContains(response, "You cannot add yourself as a friend")

    def test_user_cannot_add_a_friend_they_are_already_friends_with(self):
        """Test a user cannot add a friend they are already friends with."""
        self.client.force_login(self.user)
        self.user.friends.add(self.user2)
        self.user2.friends.add(self.user)
        response = self.client.post(
            reverse("users:friend_add"), {"user": self.user2.username}, follow=True
        )
        self.assertEqual(FriendRequest.objects.count(), 0)
        self.assertContains(response, f"{self.user2.name} is already your friend")

    def test_adding_a_friend_and_accepting_it(self):
        """Test adding a friend and accepting it."""
        self.client.force_login(self.user)
        self.client.post(reverse("users:friend_add"), {"user": self.user2.username})
        self.assertEqual(FriendRequest.objects.count(), 1)
        self.assertEqual(FriendRequest.objects.first().user_from, self.user)
        self.assertEqual(FriendRequest.objects.first().user_to, self.user2)

        self.client.force_login(self.user2)
        self.client.post(
            reverse("users:friend_request_accept", args=[FriendRequest.objects.first().pk])
        )
        self.assertEqual(FriendRequest.objects.count(), 0)
        self.assertIn(self.user2, self.user.friends.all())
        self.assertIn(self.user, self.user2.friends.all())

    def test_creating_a_duplicate_friend_request(self):
        """Test creating a duplicate friend request."""
        self.client.force_login(self.user)
        self.client.post(reverse("users:friend_add"), {"user": self.user2.username})
        self.assertEqual(FriendRequest.objects.count(), 1)
        self.assertEqual(FriendRequest.objects.first().user_from, self.user)
        self.assertEqual(FriendRequest.objects.first().user_to, self.user2)

        response = self.client.post(
            reverse("users:friend_add"), {"user": self.user2.username}, follow=True
        )
        self.assertEqual(FriendRequest.objects.count(), 1)
        self.assertContains(response, "A friend request already exists for this user")

    def test_deleting_a_friend_request_as_the_sending_user(self):
        """Test deleting a friend request."""
        self.client.force_login(self.user)
        self.client.post(reverse("users:friend_add"), {"user": self.user2.username})
        self.assertEqual(FriendRequest.objects.count(), 1)
        self.assertEqual(FriendRequest.objects.first().user_from, self.user)
        self.assertEqual(FriendRequest.objects.first().user_to, self.user2)

        self.client.post(
            reverse("users:friend_request_delete", args=[FriendRequest.objects.first().pk])
        )
        self.assertEqual(FriendRequest.objects.count(), 0)

    def test_deleting_a_friend_request_as_the_receiving_user(self):
        """Test deleting a friend request."""
        self.client.force_login(self.user)
        self.client.post(reverse("users:friend_add"), {"user": self.user2.username})
        self.assertEqual(FriendRequest.objects.count(), 1)
        self.assertEqual(FriendRequest.objects.first().user_from, self.user)
        self.assertEqual(FriendRequest.objects.first().user_to, self.user2)

        self.client.force_login(self.user2)
        self.client.post(
            reverse("users:friend_request_delete", args=[FriendRequest.objects.first().pk])
        )
        self.assertEqual(FriendRequest.objects.count(), 0)

    def test_deleting_a_friend_request_as_a_non_involved_user(self):
        """Test deleting a friend request."""
        self.client.force_login(self.user)
        self.client.post(reverse("users:friend_add"), {"user": self.user2.username})
        self.assertEqual(FriendRequest.objects.count(), 1)
        self.assertEqual(FriendRequest.objects.first().user_from, self.user)
        self.assertEqual(FriendRequest.objects.first().user_to, self.user2)

        self.client.force_login(self.user3)
        self.client.post(
            reverse("users:friend_request_delete", args=[FriendRequest.objects.first().pk])
        )
        self.assertEqual(FriendRequest.objects.count(), 1)

    def test_removing_a_friend(self):
        """Test removing a friend."""
        self.client.force_login(self.user)
        self.user.friends.add(self.user2)
        self.user2.friends.add(self.user)
        self.client.post(reverse("users:friend_remove", args=[self.user2.username]))
        self.assertNotIn(self.user2, self.user.friends.all())
        self.assertNotIn(self.user, self.user2.friends.all())

    def test_friends_page_with_get_parameters_for_user_to_add(self):
        """Test that the friends page works when a user is specified."""
        self.client.force_login(self.user)
        response = self.client.get(reverse("users:friends") + "?u=this_is_a_username")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "this_is_a_username")

    def test_friend_remove_view_with_a_user_that_is_not_a_friend(self):
        """Test that the friend remove view returns a 404 if the user is not a friend."""
        self.client.force_login(self.user)
        response = self.client.post(reverse("users:friend_remove", args=[self.user2.username]))
        self.assertEqual(response.status_code, 404)

    def test_accepting_a_friend_request_that_the_user_is_not_part_of(self):
        """Test that the friend request accept view returns a 404 if an invalid user."""
        self.client.force_login(self.user)
        fr = FriendRequest.objects.create(user_from=self.user2, user_to=self.user3)
        response = self.client.post(reverse("users:friend_request_accept", args=[fr.pk]))
        self.assertEqual(response.status_code, 403)
