import uuid
from unittest import mock

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import Client, TestCase, tag
from django.urls import reverse
from django.utils import timezone
from logger.models import Trip, TripReport

from ..models import avatar_upload_path

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
            content="Test content",
        )

        self.assertEqual(self.user.reports.count(), 1)
        self.assertEqual(self.user.reports.first(), trip_report)

    def test_avatar_upload_path(self):
        instance = mock.MagicMock()
        instance.uuid = uuid.uuid4()
        filename = "test.png"
        path = avatar_upload_path(instance, filename)
        self.assertEqual(path, f"avatars/{instance.uuid}/avatar.png")


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
        self.assertFalse(user.has_verified_email)
        self.assertEqual(user.name, "Test")
        self.assertEqual(user.username, "testregistration")

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
        self.assertTrue(user.has_verified_email)

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
        self.client.post(
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
        user_count = User.objects.count()
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
        self.assertEqual(User.objects.count(), user_count)

    def test_user_registration_with_duplicate_username(self):
        """Test user registration view with duplicate username"""
        user_count = User.objects.count()
        response = self.client.post(
            reverse("users:register"),
            {
                "name": "Test",
                "email": "dupeusername@caves.app",
                "username": "testuser",
                "password1": "this_is_a_password",
                "password2": "this_is_a_password",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Username already taken.")
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(User.objects.count(), user_count)

    def test_change_user_email_with_invalid_password(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("users:account_settings"),
            {
                "email": "new-email@caves.app",
                "password": "invalid",
                "email_submit": "Save",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The password you have entered is not correct")

    def test_change_user_email_with_email_already_in_use(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("users:account_settings"),
            {
                "email": self.user.email,
                "password": "password",
                "email_submit": "Save",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "That email is already in use")

    def test_change_user_email(self):
        """Test changing a user's email address"""
        self.client.force_login(self.user)

        # Submit the change email form
        response = self.client.post(
            reverse("users:account_settings"),
            {
                "email": "new-email@caves.app",
                "password": "password",
                "email_submit": "Save",
            },
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
        verify_code = mail.outbox[0].body.split("ode:")[1].split("If y")[0].strip()

        # Test verification with invalid code
        response = self.client.post(
            reverse("users:verify_email_change"),
            {"verify_code": "invalid"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "Email verification code is not valid or has expired"
        )

        # Test verification with valid code
        response = self.client.post(
            reverse("users:verify_email_change"),
            {"verify_code": verify_code},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "Your email address has been verified and updated."
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
            reverse("users:profile_update"),
            {
                "name": "New",
                "username": "newusername",
                "location": "Testing New Location",
                "bio": "This is a bio for testing.",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your profile has been updated.")

        # Check the user details have been updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, "New")
        self.assertEqual(self.user.username, "newusername")
        self.assertEqual(self.user.location, "Testing New Location")
        self.assertEqual(self.user.bio, "This is a bio for testing.")

    def test_submit_updates_to_settings(self):
        """Test submitting updates to a user's settings"""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("users:account_settings"),
            {
                "privacy": "Friends",
                "timezone": "US/Central",
                "units": "Imperial",
                "public_statistics": True,
                "settings_submit": "Save",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your settings have been updated.")

        # Check the user details have been updated
        self.user.refresh_from_db()
        from zoneinfo import ZoneInfo

        self.assertEqual(self.user.privacy, self.user.FRIENDS)
        self.assertEqual(self.user.timezone, ZoneInfo("US/Central"))
        self.assertEqual(self.user.units, self.user.IMPERIAL)
        self.assertTrue(self.user.public_statistics)

    def test_submit_invalid_updates_to_profile(self):
        """Test submitting invalid updates to a user's profile"""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("users:profile_update"),
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
            reverse("users:account_settings"),
            {
                "old_password": "password",
                "new_password1": "new_password",
                "new_password2": "new_password",
                "password_submit": "Save",
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

        response = self.client.get(trip.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "3281ft")

        response = self.client.get(reverse("log:user", args=[self.user.username]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "3281ft")

        # Test metric
        self.user.units = self.user.METRIC
        self.user.save()

        response = self.client.get(trip.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "1000m")

        response = self.client.get(reverse("log:user", args=[self.user.username]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "1000m")
