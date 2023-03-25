from django.test import TestCase, Client
from django.contrib.auth import get_user_model


class UserTestCase(TestCase):
    def setUp(self):
        # Test user to enable trip creation
        user = get_user_model().objects.create_user(
            email="user_test@test.com",
            username="usertestusername",
            password="password",
            first_name="Firstname",
            last_name="Lastname",
        )
        user.is_active = True
        user.save()

    def test_user_privacy(self):
        """Test CavingUser.is_public and CavingUser.is_private"""
        user = get_user_model().objects.get(email="user_test@test.com")

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
