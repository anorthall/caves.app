from django.test import TestCase, Client
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core import mail
from .models import Trip


class UserTestCase(TestCase):
    def setUp(self):
        # Reduce log level to avoid 404 error
        import logging

        logger = logging.getLogger("django.request")
        self.previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)

        # Test user to enable trip creation
        user = get_user_model().objects.create_user(
            email="user@caves.app",
            username="username",
            password="password",
            first_name="Firstname",
            last_name="Lastname",
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
        user = get_user_model().objects.get(email="user@caves.app")

        # Test where Privacy is Private
        user.privacy = get_user_model().PRIVATE
        self.assertEqual(user.privacy, get_user_model().PRIVATE)
        self.assertTrue(user.is_private)
        self.assertFalse(user.is_public)

        # Test where Privacy is Public
        user.privacy = get_user_model().PUBLIC
        self.assertEqual(user.privacy, get_user_model().PUBLIC)
        self.assertFalse(user.is_private)
        self.assertTrue(user.is_public)

    def test_has_trips_property(self):
        """Test CavingUser.has_trips property"""
        # Test with no trips
        user = get_user_model().objects.get(email="user@caves.app")
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
        user = get_user_model().objects.get(email="user@caves.app")
        self.assertFalse(user.is_staff)

        # Test when a superuser
        user.is_superuser = True
        user.save()
        self.assertTrue(user.is_staff)


class UserIntegrationTestCase(TestCase):
    def setUp(self):
        self.enabled = get_user_model().objects.create_user(
            email="enabled@user.app",
            username="testuser",
            password="password",
            first_name="Firstname",
            last_name="Lastname",
        )
        self.enabled.is_active = True
        self.enabled.save()

        self.disabled = get_user_model().objects.create_user(
            email="disabled@user.app",
            username="testuser2",
            password="password",
            first_name="Firstname",
            last_name="Lastname",
        )
        self.disabled.is_active = False
        self.disabled.save()

        self.superuser = get_user_model().objects.create_superuser(
            email="super@user.app",
            username="testuser3",
            password="password",
            first_name="Firstname",
            last_name="Lastname",
        )
        self.superuser.is_active = True
        self.superuser.save()

    def test_status_200_on_all_pages(self):
        """Test all pages return status code 200"""
        client = Client()
        client.login(email="super@user.app", password="password")

        # Test pages logged in
        logged_in_pages = [
            "/account/update/",
            "/account/email/",
            "/account/profile/",
            "/account/password/",
        ]
        for page in logged_in_pages:
            response = client.get(page)
            self.assertEqual(response.status_code, 200, msg="Error on page: " + page)

        # Test pages logged out
        client.logout()
        logged_out_pages = [
            "/account/login/",
            "/account/password/reset/",
            "/account/password/reset/confirm/abc/abc/",
            "/account/register/",
            "/account/verify/",
            "/account/verify/email/",
            "/account/verify/resend/",
        ]
        for page in logged_out_pages:
            response = client.get(page)
            self.assertEqual(response.status_code, 200, msg="Error on page: " + page)

        # Test logout returns 302
        response = client.get("/account/logout/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/")

    def test_user_login(self):
        """Test login for users"""
        client = Client()
        response = client.post(
            "/account/login/", {"email": "enabled@user.app", "password": "password"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/")

        response = client.get("/")
        self.assertContains(response, "Now logged in as enabled@user.app")

    def test_disabled_user_login(self):
        """Test login for disabled users"""
        client = Client()
        response = client.post(
            "/account/login/", {"email": "disabled@user.app", "password": "password"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "The username and password provided do not match any account"
        )

    def test_login_with_invalid_post_data(self):
        """Test login with invalid post data"""
        client = Client()
        response = client.post("/account/login/", {"invalid-data": "invalid-data"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "The username and password provided do not match any account"
        )

    def test_user_registration(self):
        """Test user registration process, including email verification"""
        client = Client()
        response = client.post(
            "/account/register/",
            {
                "first_name": "Test",
                "last_name": "User",
                "email": "test_register@user.app",
                "username": "testregistration",
                "password1": "this_is_a_password",
                "password2": "this_is_a_password",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/account/verify/")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject, "Welcome to caves.app - verify your email"
        )

        # Get the verification code
        verify_code = mail.outbox[0].body.split("ode:")[1].split("If y")[0].strip()

        # Load the user
        user = get_user_model().objects.get(email="test_register@user.app")
        self.assertFalse(user.is_active)
        self.assertEquals(user.first_name, "Test")
        self.assertEquals(user.last_name, "User")
        self.assertEquals(user.username, "testregistration")

        # Test resending verification email with invalid email
        response = client.post("/account/verify/resend/", {"email": "blah@blah.blah"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "the verification email has been resent")
        self.assertEqual(len(mail.outbox), 1)

        # Test resending verification email with valid email
        response = client.post(
            "/account/verify/resend/", {"email": "test_register@user.app"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "the verification email has been resent")
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(
            mail.outbox[1].subject, "Welcome to caves.app - verify your email"
        )

        # Test verification with invalid code
        response = client.get("/account/verify/?verify_code=invalid")
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "Email verification code is not valid or has expired"
        )

        # Test verification with valid code
        response = client.get(
            "/account/verify/?verify_code=" + verify_code, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "Welcome, Test. Your registration has been completed"
        )

        # Test user is now active
        user.refresh_from_db()
        self.assertTrue(user.is_active)

        # Test verification pages redirect to index when logged in
        response = client.get("/account/verify/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/")

        response = client.get("/account/verify/resend/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/")

        # Test resending verification email now the user is active
        client.logout()
        response = client.post(
            "/account/verify/resend/", {"email": "test_register@user.app"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "the verification email has been resent")
        self.assertEqual(len(mail.outbox), 2)

    def test_user_registration_with_invalid_data(self):
        """Test user registration view with invalid data"""
        client = Client()
        response = client.post(
            "/account/register/",
            {
                "first_name": "Test",
                "last_name": "User",
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
        client = Client()
        user = self.enabled
        client.login(email=user.email, password="password")

        # Submit the change email form
        response = client.post(
            "/account/email/",
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
        self.assertEqual(mail.outbox[1].to, [user.email])

        # Check for verification code
        self.assertEqual(mail.outbox[0].subject, "Verify your change of email")
        self.assertEqual(mail.outbox[0].to, ["new-email@caves.app"])
        verify_url = mail.outbox[0].body.split("ode:")[1].split("If y")[0].strip()

        # Test verification with invalid code
        response = client.get("/account/verify/email/?verify_code=invalid")
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "Email verification code is not valid or has expired"
        )

        # Test verification with valid code
        response = client.get(
            "/account/verify/email/?verify_code=" + verify_url, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "Your new email address, new-email@caves.app, has been verified."
        )
        user.refresh_from_db()
        self.assertEqual(user.email, "new-email@caves.app")

    def test_user_profile_page(self):
        """Test user profile page"""
        client = Client()
        user = self.enabled
        client.login(email=user.email, password="password")
        response = client.get("/account/profile/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, user.full_name)
        self.assertContains(response, user.email)
        self.assertContains(response, user.username)
        self.assertContains(response, user.privacy)
        self.assertContains(response, "Europe/London")
        self.assertContains(
            response, "If you select a trip to be public, the notes will be hidden."
        )
        self.assertContains(
            response, "Public statistics are disabled as your profile is private."
        )
        self.assertContains(response, "Change password")
        self.assertContains(response, "Change email")
        self.assertContains(response, "Edit profile")

    def test_submit_updates_to_profile(self):
        """Test submitting updates to a user's profile"""
        client = Client()
        user = self.enabled
        client.login(email=user.email, password="password")
        response = client.post(
            "/account/update/",
            {
                "first_name": "New",
                "last_name": "Name",
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
        self.assertContains(response, "Your details have been updated")

        # Check the user details have been updated
        user.refresh_from_db()
        from zoneinfo import ZoneInfo

        self.assertEqual(user.first_name, "New")
        self.assertEqual(user.last_name, "Name")
        self.assertEqual(user.username, "newusername")
        self.assertEqual(user.location, "Testing New Location")
        self.assertEqual(user.privacy, user.PUBLIC)
        self.assertEqual(user.timezone, ZoneInfo("US/Central"))
        self.assertEqual(user.units, user.IMPERIAL)
        self.assertTrue(user.show_statistics)
        self.assertEqual(user.bio, "This is a bio for testing.")

    def test_change_user_password(self):
        """Test changing a user's password"""
        client = Client()
        user = self.enabled
        client.login(email=user.email, password="password")
        response = client.post(
            "/account/password/",
            {
                "old_password": "password",
                "new_password1": "new_password",
                "new_password2": "new_password",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your password has been updated.")
        user.refresh_from_db()
        self.assertTrue(user.check_password("new_password"))
