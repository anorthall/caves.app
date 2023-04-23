from django.contrib.auth import get_user_model
from django.test import Client, TestCase, tag
from django.urls import reverse
from django.utils import timezone
from logger.models import Trip
from users.models import FriendRequest

User = get_user_model()


@tag("fast", "core", "pageload")
class TestAllPagesLoad(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@caves.app",
            username="testuser",
            password="password",
            name="Test User",
        )
        self.user.is_active = True
        self.user.save()

    def test_index_page_loads(self):
        """Test that the home page loads"""
        client = Client()
        response = client.get(reverse("log:index"))
        self.assertEqual(response.status_code, 200)

    def test_new_user_index_page_loads(self):
        """Test that the home page loads for a new user"""
        client = Client()
        client.login(email="test@caves.app", password="password")
        response = client.get(reverse("log:index"))
        self.assertEqual(response.status_code, 200)

    def test_established_user_index_page_loads(self):
        """Test that the home page loads for an established user"""
        client = Client()
        client.login(email="test@caves.app", password="password")
        for i in range(50):
            Trip.objects.create(
                user=self.user, cave_name="Test Trip {}".format(i), start=timezone.now()
            ).save()

        response = client.get(reverse("log:index"))
        self.assertEqual(response.status_code, 200)

    def test_login_page_loads(self):
        """Test that the login page loads"""
        client = Client()
        response = client.get(reverse("users:login"))
        self.assertEqual(response.status_code, 200)

    def test_logout_page_loads(self):
        """Test that the logout page loads"""
        client = Client()
        response = client.get(reverse("users:logout"))
        self.assertEqual(response.status_code, 302)

    def test_register_page_loads(self):
        """Test that the register page loads"""
        client = Client()
        response = client.get(reverse("users:register"))
        self.assertEqual(response.status_code, 200)

    def test_help_page_loads(self):
        """Test that the help page loads"""
        client = Client()
        response = client.get(reverse("core:help"))
        self.assertEqual(response.status_code, 200)

    def test_about_page_loads(self):
        """Test that the about page loads"""
        client = Client()
        response = client.get(reverse("core:about"))
        self.assertEqual(response.status_code, 200)

    def test_verify_new_account_page_loads(self):
        """Test that the verify new account page loads"""
        client = Client()
        response = client.get(reverse("users:verify-new-account"))
        self.assertEqual(response.status_code, 200)

    def test_verify_email_resend_page_loads(self):
        """Test that the verify email resend page loads"""
        client = Client()
        response = client.get(reverse("users:verify-resend"))
        self.assertEqual(response.status_code, 200)

    def test_password_reset_page_loads(self):
        """Test that the password reset page loads"""
        client = Client()
        response = client.get(reverse("users:password-reset"))
        self.assertEqual(response.status_code, 200)

    def test_password_reset_confirm_page_loads(self):
        """Test that the password reset confirm page loads"""
        client = Client()
        response = client.get(
            reverse(
                "users:password-reset-confirm",
                kwargs={"uidb64": "test", "token": "test"},
            )
        )
        self.assertEqual(response.status_code, 200)

    def test_password_change_page_loads(self):
        """Test that the password change page loads"""
        client = Client()
        client.login(email="test@caves.app", password="password")
        response = client.get(reverse("users:password"))
        self.assertEqual(response.status_code, 200)

    def test_email_change_page_loads(self):
        """Test that the email change page loads"""
        client = Client()
        client.login(email="test@caves.app", password="password")
        response = client.get(reverse("users:email"))
        self.assertEqual(response.status_code, 200)

    def test_verify_email_change_page_loads(self):
        """Test that the verify email change page loads"""
        client = Client()
        client.login(email="test@caves.app", password="password")
        response = client.get(reverse("users:verify-email-change"))
        self.assertEqual(response.status_code, 200)

    def test_account_page_loads(self):
        """Test that the account page loads"""
        client = Client()
        client.login(email="test@caves.app", password="password")
        response = client.get(reverse("users:account"))
        self.assertEqual(response.status_code, 200)

    def test_account_update_page_loads(self):
        """Test that the account update page loads"""
        client = Client()
        client.login(email="test@caves.app", password="password")
        response = client.get(reverse("users:account_update"))
        self.assertEqual(response.status_code, 200)

    def test_friends_page_loads_without_friends(self):
        """Test that the friends page loads without friends"""
        client = Client()
        client.login(email="test@caves.app", password="password")
        response = client.get(reverse("users:friends"))
        self.assertEqual(response.status_code, 200)

    def test_friends_page_loads_with_friends_and_requests(self):
        """Test that the friends page loads with friends and requests"""
        client = Client()
        client.login(email="test@caves.app", password="password")
        for i in range(10):
            u = User.objects.create_user(
                email=f"test_1_{i}@caves.app",
                username=f"testuser_1_{i}",
                password="password",
                name=f"Test User {i}",
            )

            u.profile.friends.add(self.user)
            self.user.profile.friends.add(u)

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

        response = client.get(reverse("users:friends"))
        self.assertEqual(response.status_code, 200)

    def test_user_trip_list_page_loads(self):
        """Test that the user trip list page loads"""
        client = Client()
        client.login(email="test@caves.app", password="password")
        response = client.get(
            reverse("log:user", kwargs={"username": self.user.username})
        )
        self.assertEqual(response.status_code, 200)

    def test_user_trip_list_page_loads_with_trips(self):
        """Test that the user trip list page loads with trips"""
        client = Client()
        client.login(email="test@caves.app", password="password")
        for i in range(250):
            t = Trip.objects.create(
                cave_name=f"Test Trip {i}", start=timezone.now(), user=self.user
            )
            t.save()
        response = client.get(
            reverse("log:user", kwargs={"username": self.user.username})
        )
        self.assertEqual(response.status_code, 200)

    def test_trip_page_loads(self):
        """Test that the trip page loads"""
        client = Client()
        client.login(email="test@caves.app", password="password")
        trip = Trip.objects.create(
            cave_name="Test Trip", start=timezone.now(), user=self.user
        )
        trip.save()
        response = client.get(reverse("log:trip_detail", kwargs={"pk": trip.pk}))
        self.assertEqual(response.status_code, 200)

    def test_trip_update_page_loads(self):
        """Test that the trip update page loads"""
        client = Client()
        client.login(email="test@caves.app", password="password")
        trip = Trip.objects.create(
            cave_name="Test Trip", start=timezone.now(), user=self.user
        )
        trip.save()
        response = client.get(reverse("log:trip_update", kwargs={"pk": trip.pk}))
        self.assertEqual(response.status_code, 200)

    def test_trip_list_redirect_page_loads(self):
        """Test that the trip list redirect page loads"""
        client = Client()
        client.login(email="test@caves.app", password="password")
        response = client.get(reverse("log:trip_list"), follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, reverse("log:user", kwargs={"username": self.user.username})
        )

    def test_trip_export_page_loads(self):
        """Test that the trip export page loads"""
        client = Client()
        client.login(email="test@caves.app", password="password")
        response = client.get(reverse("log:export"))
        self.assertEqual(response.status_code, 200)

    # TODO: Add rest of tests for logger.urls
