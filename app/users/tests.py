from django.contrib.auth import get_user_model
from django.core import mail
from django.test import Client, TestCase, tag
from django.urls import reverse
from django.utils import timezone
from users.templatetags.user import user as user_templatetag

from .models import Trip

User = get_user_model()


@tag("unit", "users", "fast")
class UserTestCase(TestCase):
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

    def tearDown(self):
        """Reset the log level back to normal"""
        import logging

        logger = logging.getLogger("django.request")
        logger.setLevel(self.previous_level)

    def test_user_privacy(self):
        """Test CavingUser.is_public and CavingUser.is_private"""
        user = User.objects.get(email="user@caves.app")

        # Test where Privacy is Private
        user.settings.privacy = user.settings.PRIVATE
        self.assertEqual(user.settings.privacy, user.settings.PRIVATE)
        self.assertTrue(user.is_private)
        self.assertFalse(user.is_public)

        # Test where Privacy is Public
        user.settings.privacy = user.settings.PUBLIC
        self.assertEqual(user.settings.privacy, user.settings.PUBLIC)
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
            {"email": "enabled@user.app", "password": "password"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("log:index"))

        response = self.client.get(reverse("log:index"))
        self.assertContains(response, "Now logged in as enabled@user.app")

    def test_disabled_user_login(self):
        """Test login for disabled users"""
        response = self.client.post(
            reverse("users:login"),
            {"email": "disabled@user.app", "password": "password"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "The username and password provided do not match any account"
        )

    def test_login_with_invalid_post_data(self):
        """Test login with invalid post data"""
        response = self.client.post(
            reverse("users:login"), {"invalid-data": "invalid-data"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "The username and password provided do not match any account"
        )

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
        self.assertEqual(response.url, reverse("users:verify-new-account"))
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
            reverse("users:verify-resend"), {"email": "blah@blah.blah"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "the verification email has been resent")
        self.assertEqual(len(mail.outbox), 1)

        # Test resending verification email with valid email
        response = self.client.post(
            reverse("users:verify-resend"), {"email": "test_register@user.app"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "the verification email has been resent")
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(
            mail.outbox[1].subject, "Welcome to caves.app - verify your email"
        )

        # Test verification with invalid code
        response = self.client.get(
            reverse("users:verify-new-account") + "?verify_code=invalid"
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "Email verification code is not valid or has expired"
        )

        # Test verification with valid code
        response = self.client.get(
            reverse("users:verify-new-account") + "?verify_code=" + verify_code,
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
        response = self.client.get(reverse("users:verify-new-account"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("log:index"))

        response = self.client.get(reverse("users:verify-resend"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("log:index"))

        # Test resending verification email now the user is active
        self.client.logout()
        response = self.client.post(
            reverse("users:verify-resend"), {"email": "test_register@user.app"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "the verification email has been resent")
        self.assertEqual(len(mail.outbox), 2)

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
            reverse("users:verify-email-change") + "?verify_code=invalid"
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "Email verification code is not valid or has expired"
        )

        # Test verification with valid code
        response = self.client.get(
            reverse("users:verify-email-change") + "?verify_code=" + verify_url,
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
        response = self.client.get(reverse("users:account"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.name)
        self.assertContains(response, self.user.email)
        self.assertContains(response, self.user.username)
        self.assertContains(response, self.user.settings.privacy)
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
                "show_statistics": True,
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
        self.assertEqual(self.user.profile.location, "Testing New Location")
        self.assertEqual(self.user.settings.privacy, self.user.settings.PUBLIC)
        self.assertEqual(self.user.settings.timezone, ZoneInfo("US/Central"))
        self.assertEqual(self.user.settings.units, self.user.settings.IMPERIAL)
        self.assertTrue(self.user.settings.show_statistics)
        self.assertEqual(self.user.profile.bio, "This is a bio for testing.")

    def test_change_user_password(self):
        """Test changing a user's password"""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("users:password"),
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
