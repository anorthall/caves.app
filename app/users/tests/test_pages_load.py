from django.contrib.auth import get_user_model
from django.test import Client, TestCase, tag
from django.urls import reverse
from users.models import FriendRequest

User = get_user_model()


@tag("fast", "views", "users")
class TestUsersPagesLoad(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@caves.app",
            username="testuser",
            password="password",
            name="Test User",
        )
        self.user.is_active = True
        self.user.save()

        self.client = Client()

    def test_login_page_loads(self):
        """Test that the login page loads"""
        response = self.client.get(reverse("users:login"))
        self.assertEqual(response.status_code, 200)

    def test_logout_page_loads(self):
        """Test that the logout page loads"""
        response = self.client.get(reverse("users:logout"))
        self.assertEqual(response.status_code, 302)

    def test_register_page_loads(self):
        """Test that the register page loads"""
        response = self.client.get(reverse("users:register"))
        self.assertEqual(response.status_code, 200)

    def test_verify_new_account_page_loads(self):
        """Test that the verify new account page loads"""
        response = self.client.get(reverse("users:verify_new_account"))
        self.assertEqual(response.status_code, 200)

    def test_verify_email_resend_page_loads(self):
        """Test that the verify email resend page loads"""
        response = self.client.get(reverse("users:verify_resend"))
        self.assertEqual(response.status_code, 200)

    def test_password_reset_page_loads(self):
        """Test that the password reset page loads"""
        response = self.client.get(reverse("users:password_reset"))
        self.assertEqual(response.status_code, 200)

    def test_password_reset_confirm_page_loads(self):
        """Test that the password reset confirm page loads"""
        response = self.client.get(
            reverse(
                "users:password_reset_confirm",
                kwargs={"uidb64": "test", "token": "test"},
            )
        )
        self.assertEqual(response.status_code, 200)

    def test_password_change_page_loads(self):
        """Test that the password change page loads"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("users:password_update"))
        self.assertEqual(response.status_code, 200)

    def test_email_change_page_loads(self):
        """Test that the email change page loads"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("users:email"))
        self.assertEqual(response.status_code, 200)

    def test_verify_email_change_page_loads(self):
        """Test that the verify email change page loads"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("users:verify_email_change"))
        self.assertEqual(response.status_code, 200)

    def test_account_page_loads(self):
        """Test that the account page loads"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("users:account_detail"))
        self.assertEqual(response.status_code, 200)

    def test_profile_update_page_loads(self):
        """Test that the profile update page loads"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("users:profile_update"))
        self.assertEqual(response.status_code, 200)

    def test_settings_update_page_loads(self):
        """Test that the settings update page loads"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("users:settings_update"))
        self.assertEqual(response.status_code, 200)

    def test_profile_picture_update_page_loads(self):
        """Test that the profile picture update page loads"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("users:profile_photo_update"))
        self.assertEqual(response.status_code, 200)

    def test_friends_page_loads_without_friends(self):
        """Test that the friends page loads without friends"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("users:friends"))
        self.assertEqual(response.status_code, 200)

    def test_friends_page_loads_with_friends_and_requests(self):
        """Test that the friends page loads with friends and requests"""
        self.client.force_login(self.user)
        for i in range(10):
            u = User.objects.create_user(
                email=f"test_1_{i}@caves.app",
                username=f"testuser_1_{i}",
                password="password",
                name=f"Test User {i}",
            )

            u.friends.add(self.user)
            self.user.friends.add(u)

        for i in range(10):
            u = User.objects.create_user(
                email=f"test_2_{i}@caves.app",
                username=f"testuser_2_{i}",
                password="password",
                name=f"Test User {i}",
            )

            if i < 5:
                FriendRequest.objects.create(user_from=self.user, user_to=u).save()
            else:
                FriendRequest.objects.create(user_from=u, user_to=self.user).save()

        response = self.client.get(reverse("users:friends"))
        self.assertEqual(response.status_code, 200)

    def test_custom_fields_page_loads(self):
        """Test that the custom fields page loads"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("users:custom_fields_update"))
        self.assertEqual(response.status_code, 200)

    def test_notifications_list_page_loads(self):
        """Test that the notifications list page loads"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("users:notifications"))
        self.assertEqual(response.status_code, 200)
