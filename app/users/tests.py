from django.contrib.auth import get_user_model
from django.core import mail
from django.test import Client, TestCase, tag
from django.urls import reverse
from django.utils import timezone
from logger.models import Trip, TripReport
from users.models import FriendRequest
from users.templatetags.user import user as user_templatetag

User = get_user_model()


@tag("unit", "users", "fast")
class UserUnitTests(TestCase):
    def setUp(self):
        # Reduce log level to avoid 404 error
        import logging

        logger = logging.getLogger("django.request")
        self.previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)

        # Test user to enable trip creation
        user = User.objects.create_user(
            email="user@caves.app",
            username="username",
            password="password",
            name="Firstname",
        )
        user.is_active = True
        user.save()

        self.user = user

    def tearDown(self):
        """Reset the log level back to normal"""
        import logging

        logger = logging.getLogger("django.request")
        logger.setLevel(self.previous_level)

    def test_user_privacy(self):
        """Test CavingUser.is_public and CavingUser.is_private"""
        user = User.objects.get(email="user@caves.app")

        # Test where Privacy is Private
        user.privacy = user.PRIVATE
        self.assertEqual(user.privacy, user.PRIVATE)
        self.assertTrue(user.is_private)
        self.assertFalse(user.is_public)

        # Test where Privacy is Public
        user.privacy = user.PUBLIC
        self.assertEqual(user.privacy, user.PUBLIC)
        self.assertFalse(user.is_private)
        self.assertTrue(user.is_public)

    def test_has_trips_property(self):
        """Test CavingUser.has_trips property"""
        # Test with no trips
        user = User.objects.get(email="user@caves.app")
        self.assertFalse(user.has_trips)

        # Test with trips
        Trip.objects.create(
            user=user,
            cave_name="Test Cave",
            start=timezone.now(),
        )
        self.assertTrue(user.has_trips)

    def test_is_staff_property(self):
        """Test CavingUser.is_staff property"""
        # Test when not a superuser
        user = User.objects.get(email="user@caves.app")
        self.assertFalse(user.is_staff)

        # Test when a superuser
        user.is_superuser = True
        user.save()
        self.assertTrue(user.is_staff)

    def test_create_user_with_no_email(self):
        """Test the create user function with an empty string for an email"""
        with self.assertRaises(ValueError):
            User.objects.create_user(
                email="",
                username="username",
                name="name",
            )

    def test_create_user_with_no_username(self):
        """Test the create user function with an empty string for a username"""
        with self.assertRaises(ValueError):
            User.objects.create_user(
                email="test@caves.app",
                username="",
                name="name",
            )

    def test_create_user_with_no_name(self):
        """Test the create user function with an empty string for a name"""
        with self.assertRaises(ValueError):
            User.objects.create_user(
                email="test@caves.app",
                username="username",
                name="",
            )

    def test_user_cannot_have_self_as_friend(self):
        """Test that a user cannot have themselves as a friend"""
        self.user.friends.add(self.user)
        self.user.save()
        self.user.refresh_from_db()
        self.assertEqual(self.user.friends.count(), 0)

    def test_user_get_short_name_function(self):
        """Test the get_short_name function of the CavingUser model"""
        self.assertEqual(self.user.get_short_name(), self.user.name)

    def test_user_get_full_name_function(self):
        """Test the get_full_name function of the CavingUser model"""
        self.assertEqual(self.user.get_full_name(), self.user.name)

    def test_user_trip_reports_function(self):
        """Test the reports function of the CavingUser model"""
        trip = Trip.objects.create(
            user=self.user,
            cave_name="Test Cave",
            start=timezone.now(),
        )

        trip_report = TripReport.objects.create(
            user=self.user,
            trip=trip,
            title="Test Report",
            pub_date=timezone.now().date(),
            slug="test-report",
            content="Test content",
        )

        self.assertEqual(self.user.reports.count(), 1)
        self.assertEqual(self.user.reports.first(), trip_report)


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
        """Test the __str__ method of the FriendRequest model"""
        request = FriendRequest.objects.create(
            user_from=self.user,
            user_to=self.user2,
        )
        self.assertEqual(str(request), f"{self.user} -> {self.user2}")

    def test_notification_str(self):
        """Test the __str__ method of the Notification model"""
        msg = "Notification message"
        notification = self.user.notify(msg, "/")
        self.assertEqual(str(notification), msg)


@tag("integration", "users", "fast")
class UserIntegrationTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        self.user = User.objects.create_user(
            email="enabled@user.app",
            username="testuser",
            password="password",
            name="Firstname",
        )
        self.user.is_active = True
        self.user.save()

        self.disabled = User.objects.create_user(
            email="disabled@user.app",
            username="testuser2",
            password="password",
            name="Firstname",
        )
        self.disabled.is_active = False
        self.disabled.save()

        self.superuser = User.objects.create_superuser(
            email="super@user.app",
            username="testuser3",
            password="password",
            name="Firstname",
        )
        self.superuser.is_active = True
        self.superuser.save()

    def test_user_login(self):
        """Test login for users"""
        response = self.client.post(
            reverse("users:login"),
            {"username": "enabled@user.app", "password": "password"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("log:index"))

        response = self.client.get(reverse("log:index"))
        self.assertContains(response, "You are now logged in.")

    def test_user_registration_page_redirects_when_logged_in(self):
        """Test that the user registration page redirects when already logged in"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("users:register"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("users:account_detail"))

    def test_user_registration(self):
        """Test user registration process, including email verification"""
        response = self.client.post(
            reverse("users:register"),
            {
                "name": "Test",
                "email": "test_register@user.app",
                "username": "testregistration",
                "password1": "this_is_a_password",
                "password2": "this_is_a_password",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("users:verify_new_account"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject, "Welcome to caves.app - verify your email"
        )

        # Get the verification code
        verify_code = mail.outbox[0].body.split("ode:")[1].split("If y")[0].strip()

        # Load the user
        user = User.objects.get(email="test_register@user.app")
        self.assertFalse(user.is_active)
        self.assertEquals(user.name, "Test")
        self.assertEquals(user.username, "testregistration")

        # Test resending verification email with invalid email
        response = self.client.post(
            reverse("users:verify_resend"), {"email": "blah@blah.blah"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "the verification email has been resent")
        self.assertEqual(len(mail.outbox), 1)

        # Test resending verification email with valid email
        response = self.client.post(
            reverse("users:verify_resend"), {"email": "test_register@user.app"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "the verification email has been resent")
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(
            mail.outbox[1].subject, "Welcome to caves.app - verify your email"
        )

        # Test verification with invalid code
        response = self.client.get(
            reverse("users:verify_new_account") + "?verify_code=invalid"
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "Email verification code is not valid or has expired"
        )

        # Test verification with valid code
        response = self.client.get(
            reverse("users:verify_new_account") + "?verify_code=" + verify_code,
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "Welcome, Test. Your registration has been completed"
        )

        # Test user is now active
        user.refresh_from_db()
        self.assertTrue(user.is_active)

        # Test verification pages redirect to index when logged in
        response = self.client.get(reverse("users:verify_new_account"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("log:index"))

        response = self.client.get(reverse("users:verify_resend"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("log:index"))

        # Test resending verification email now the user is active
        self.client.logout()
        response = self.client.post(
            reverse("users:verify_resend"), {"email": "test_register@user.app"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "the verification email has been resent")
        self.assertEqual(len(mail.outbox), 2)

    def test_verifying_email_for_a_deleted_user(self):
        """Test registering a user, then deleting them before they verify their email"""
        response = self.client.post(
            reverse("users:register"),
            {
                "name": "Test",
                "email": "test_register@user.app",
                "username": "testregistration",
                "password1": "this_is_a_password",
                "password2": "this_is_a_password",
            },
        )
        verify_code = mail.outbox[0].body.split("ode:")[1].split("If y")[0].strip()
        user = User.objects.get(email="test_register@user.app")
        user.delete()

        response = self.client.get(
            reverse("users:verify_new_account") + "?verify_code=" + verify_code,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "Email verification code is not valid or has expired."
        )

    def test_user_registration_with_invalid_data(self):
        """Test user registration view with invalid data"""
        response = self.client.post(
            reverse("users:register"),
            {
                "name": "Test",
                "email": "test_register",
                "username": "testr egistration",
                "password1": "this_is_a_password",
                "password2": "none",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Passwords do not match.")
        self.assertContains(response, "Enter a valid email address.")
        self.assertContains(response, "Enter a valid “slug” consisting of")
        self.assertEqual(len(mail.outbox), 0)

    def test_change_user_email_with_invalid_password(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("users:email"),
            {"email": "new-email@caves.app", "password": "invalid"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The password you have entered is not correct")

    def test_change_user_email_with_email_already_in_use(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("users:email"),
            {"email": self.user.email, "password": "password"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "That email is already in use")

    def test_change_user_email(self):
        """Test changing a user's email address"""
        self.client.force_login(self.user)

        # Submit the change email form
        response = self.client.post(
            reverse("users:email"),
            {"email": "new-email@caves.app", "password": "password"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "Please follow the instructions sent to your new email address"
        )
        self.assertEqual(len(mail.outbox), 2)

        # Check for security notification email
        self.assertEqual(mail.outbox[1].subject, "Change of email address requested")
        self.assertEqual(mail.outbox[1].to, [self.user.email])

        # Check for verification code
        self.assertEqual(mail.outbox[0].subject, "Verify your change of email")
        self.assertEqual(mail.outbox[0].to, ["new-email@caves.app"])
        verify_url = mail.outbox[0].body.split("ode:")[1].split("If y")[0].strip()

        # Test verification with invalid code
        response = self.client.get(
            reverse("users:verify_email_change") + "?verify_code=invalid"
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "Email verification code is not valid or has expired"
        )

        # Test verification with valid code
        response = self.client.get(
            reverse("users:verify_email_change") + "?verify_code=" + verify_url,
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "Your new email address, new-email@caves.app, has been verified."
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "new-email@caves.app")

    def test_user_profile_page(self):
        """Test user profile page"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("users:account_detail"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.name)
        self.assertContains(response, self.user.email)
        self.assertContains(response, self.user.username)
        self.assertContains(response, self.user.privacy)
        self.assertContains(response, "Europe/London")
        self.assertContains(
            response, "If you select a trip to be public, the notes will be hidden."
        )
        self.assertContains(
            response, "Public statistics are disabled as your profile is private."
        )

    def test_submit_updates_to_profile(self):
        """Test submitting updates to a user's profile"""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("users:account_update"),
            {
                "name": "New",
                "username": "newusername",
                "location": "Testing New Location",
                "privacy": "Public",
                "timezone": "US/Central",
                "units": "Imperial",
                "public_statistics": True,
                "bio": "This is a bio for testing.",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your profile has been updated.")

        # Check the user details have been updated
        self.user.refresh_from_db()
        from zoneinfo import ZoneInfo

        self.assertEqual(self.user.name, "New")
        self.assertEqual(self.user.username, "newusername")
        self.assertEqual(self.user.location, "Testing New Location")
        self.assertEqual(self.user.privacy, self.user.PUBLIC)
        self.assertEqual(self.user.timezone, ZoneInfo("US/Central"))
        self.assertEqual(self.user.units, self.user.IMPERIAL)
        self.assertTrue(self.user.public_statistics)
        self.assertEqual(self.user.bio, "This is a bio for testing.")

    def test_submit_invalid_updates_to_profile(self):
        """Test submitting invalid updates to a user's profile"""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("users:account_update"),
            {
                "username": "spaces in username",
            },
            follow=True,
        )
        self.assertContains(response, "Enter a valid “slug” consisting of")

    def test_change_user_password(self):
        """Test changing a user's password"""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("users:password_update"),
            {
                "old_password": "password",
                "new_password1": "new_password",
                "new_password2": "new_password",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your password has been updated.")
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("new_password"))

    def test_user_distance_settings_are_applied(self):
        """Test user distance settings are applied to distances on the site"""
        self.client.force_login(self.user)
        self.user.units = self.user.IMPERIAL
        self.user.save()

        trip = Trip.objects.create(
            user=self.user,
            cave_name="Test Trip",
            start=timezone.now(),
            vert_dist_up="1000m",
        )
        trip.save()

        response = self.client.get(reverse("log:trip_detail", args=[trip.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "3281ft")

        response = self.client.get(reverse("log:user", args=[self.user.username]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "3281ft")

        # Test metric
        self.user.units = self.user.METRIC
        self.user.save()

        response = self.client.get(reverse("log:trip_detail", args=[trip.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "1000m")

        response = self.client.get(reverse("log:user", args=[self.user.username]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "1000m")

    def test_notifications_are_displayed(self):
        """Test notifications are displayed on the user's profile"""
        self.client.force_login(self.user)

        for i in range(10):
            self.user.notify(f"Test {i}", "/")

        response = self.client.get(reverse("users:account_detail"))
        for i in range(1, 5):
            self.assertNotContains(response, f"Test {i}")

        for i in range(6, 10):
            self.assertContains(response, f"Test {i}")

    def test_notification_redirect_view(self):
        """Test the notification redirect view"""
        self.client.force_login(self.user)
        pk = self.user.notify("Test", "/test/").pk
        response = self.client.get(reverse("users:notification", args=[pk]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/test/")


@tag("integration", "fast", "users")
class FriendsIntegrationTests(TestCase):
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
        """Test sending a friend request by username"""
        self.client.force_login(self.user)
        self.client.post(reverse("users:friend_add"), {"user": self.user2.username})
        self.assertEqual(FriendRequest.objects.count(), 1)
        self.assertEqual(FriendRequest.objects.first().user_from, self.user)
        self.assertEqual(FriendRequest.objects.first().user_to, self.user2)

    def test_sending_a_friend_request_by_email(self):
        """Test sending a friend request by email"""
        self.client.force_login(self.user)
        self.user2.allow_friend_email = True
        self.user2.save()
        self.client.post(reverse("users:friend_add"), {"user": self.user2.email})
        self.assertEqual(FriendRequest.objects.count(), 1)
        self.assertEqual(FriendRequest.objects.first().user_from, self.user)
        self.assertEqual(FriendRequest.objects.first().user_to, self.user2)

    def test_friend_request_disallowed_by_email(self):
        """Test sending a friend request by email is disallowed"""
        self.client.force_login(self.user)
        self.user2.allow_friend_email = False
        self.user2.save()
        self.client.post(reverse("users:friend_add"), {"user": self.user2.email})
        self.assertEqual(FriendRequest.objects.count(), 0)

    def test_friend_request_disallowed_by_username(self):
        """Test sending a friend request by username is disallowed"""
        self.client.force_login(self.user)
        self.user2.allow_friend_username = False
        self.user2.save()
        self.client.post(reverse("users:friend_add"), {"user": self.user2.username})
        self.assertEqual(FriendRequest.objects.count(), 0)

    def test_adding_self_as_friend_is_not_permitted(self):
        """Test adding self as a friend is not permitted"""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("users:friend_add"), {"user": self.user.username}, follow=True
        )
        self.assertEqual(FriendRequest.objects.count(), 0)
        self.assertContains(response, "You cannot add yourself as a friend")

    def test_user_cannot_add_a_friend_they_are_already_friends_with(self):
        """Test a user cannot add a friend they are already friends with"""
        self.client.force_login(self.user)
        self.user.friends.add(self.user2)
        self.user2.friends.add(self.user)
        response = self.client.post(
            reverse("users:friend_add"), {"user": self.user2.username}, follow=True
        )
        self.assertEqual(FriendRequest.objects.count(), 0)
        self.assertContains(response, f"{self.user2.name} is already your friend")

    def test_adding_a_friend_and_accepting_it(self):
        """Test adding a friend and accepting it"""
        self.client.force_login(self.user)
        self.client.post(reverse("users:friend_add"), {"user": self.user2.username})
        self.assertEqual(FriendRequest.objects.count(), 1)
        self.assertEqual(FriendRequest.objects.first().user_from, self.user)
        self.assertEqual(FriendRequest.objects.first().user_to, self.user2)

        self.client.force_login(self.user2)
        self.client.post(
            reverse(
                "users:friend_request_accept", args=[FriendRequest.objects.first().pk]
            )
        )
        self.assertEqual(FriendRequest.objects.count(), 0)
        self.assertIn(self.user2, self.user.friends.all())
        self.assertIn(self.user, self.user2.friends.all())

    def test_creating_a_duplicate_friend_request(self):
        """Test creating a duplicate friend request"""
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
        """Test deleting a friend request"""
        self.client.force_login(self.user)
        self.client.post(reverse("users:friend_add"), {"user": self.user2.username})
        self.assertEqual(FriendRequest.objects.count(), 1)
        self.assertEqual(FriendRequest.objects.first().user_from, self.user)
        self.assertEqual(FriendRequest.objects.first().user_to, self.user2)

        self.client.post(
            reverse(
                "users:friend_request_delete", args=[FriendRequest.objects.first().pk]
            )
        )
        self.assertEqual(FriendRequest.objects.count(), 0)

    def test_deleting_a_friend_request_as_the_receiving_user(self):
        """Test deleting a friend request"""
        self.client.force_login(self.user)
        self.client.post(reverse("users:friend_add"), {"user": self.user2.username})
        self.assertEqual(FriendRequest.objects.count(), 1)
        self.assertEqual(FriendRequest.objects.first().user_from, self.user)
        self.assertEqual(FriendRequest.objects.first().user_to, self.user2)

        self.client.force_login(self.user2)
        self.client.post(
            reverse(
                "users:friend_request_delete", args=[FriendRequest.objects.first().pk]
            )
        )
        self.assertEqual(FriendRequest.objects.count(), 0)

    def test_deleting_a_friend_request_as_a_non_involved_user(self):
        """Test deleting a friend request"""
        self.client.force_login(self.user)
        self.client.post(reverse("users:friend_add"), {"user": self.user2.username})
        self.assertEqual(FriendRequest.objects.count(), 1)
        self.assertEqual(FriendRequest.objects.first().user_from, self.user)
        self.assertEqual(FriendRequest.objects.first().user_to, self.user2)

        self.client.force_login(self.user3)
        self.client.post(
            reverse(
                "users:friend_request_delete", args=[FriendRequest.objects.first().pk]
            )
        )
        self.assertEqual(FriendRequest.objects.count(), 1)

    def test_removing_a_friend(self):
        """Test removing a friend"""
        self.client.force_login(self.user)
        self.user.friends.add(self.user2)
        self.user2.friends.add(self.user)
        self.client.post(reverse("users:friend_remove", args=[self.user2.username]))
        self.assertNotIn(self.user2, self.user.friends.all())
        self.assertNotIn(self.user, self.user2.friends.all())

    def test_friends_page_with_get_parameters_for_user_to_add(self):
        """Test that the friends page works when a user is specified"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("users:friends") + "?u=this_is_a_username")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "this_is_a_username")

    def test_friend_remove_view_with_a_user_that_is_not_a_friend(self):
        """Test that the friend remove view returns a 404 if the user is not a friend"""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("users:friend_remove", args=[self.user2.username])
        )
        self.assertEqual(response.status_code, 404)

    def test_accepting_a_friend_request_that_the_user_is_not_part_of(self):
        """Test that the friend request accept view returns a 404 if an invalid user"""
        self.client.force_login(self.user)
        fr = FriendRequest.objects.create(user_from=self.user2, user_to=self.user3)
        response = self.client.post(
            reverse("users:friend_request_accept", args=[fr.pk])
        )
        self.assertEqual(response.status_code, 404)


@tag("unit", "fast", "users")
class TemplateTagUnitTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="enabled@user.app",
            username="enabled",
            password="testpassword",
            name="Joe",
        )
        self.user.is_active = True
        self.user.save()

    def test_user_template_tag_with_non_user_object(self):
        """Test the user template tag raises TypeError when passed a non-user object"""
        self.assertRaises(TypeError, user_templatetag, None, None)
