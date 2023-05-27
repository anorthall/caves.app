from django.contrib.auth import get_user_model
from django.test import Client, TestCase, tag
from django.urls import reverse
from django.utils import timezone
from logger.models import Trip, TripReport
from users.models import FriendRequest

User = get_user_model()


@tag("fast", "pageload")
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

        self.trip = Trip.objects.create(
            user=self.user, cave_name="Test Trip", start=timezone.now()
        )

        self.report = TripReport.objects.create(
            user=self.user,
            trip=self.trip,
            title="Test Report",
            slug="test",
            content="Test Report Content",
            pub_date=timezone.now().date(),
        )

        self.client = Client()

    def test_index_page_loads(self):
        """Test that the home page loads"""
        response = self.client.get(reverse("log:index"))
        self.assertEqual(response.status_code, 200)

    def test_new_user_index_page_loads(self):
        """Test that the home page loads for a new user"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("log:index"))
        self.assertEqual(response.status_code, 200)

    def test_established_user_index_page_loads(self):
        """Test that the home page loads for an established user"""
        self.client.force_login(self.user)
        for i in range(50):
            Trip.objects.create(
                user=self.user, cave_name="Test Trip {}".format(i), start=timezone.now()
            ).save()

        response = self.client.get(reverse("log:index"))
        self.assertEqual(response.status_code, 200)

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

    def test_help_page_loads(self):
        """Test that the help page loads"""
        response = self.client.get(reverse("core:help"))
        self.assertEqual(response.status_code, 200)

    def test_help_page_loads_when_logged_in(self):
        """Test that the help page loads when logged in"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("core:help"))
        self.assertEqual(response.status_code, 200)

    def test_about_page_loads(self):
        """Test that the about page loads"""
        response = self.client.get(reverse("core:about"))
        self.assertEqual(response.status_code, 200)

    def test_about_page_loads_with_trips_with_duration(self):
        """Test that the about page loads with trips with duration"""
        self.client.force_login(self.user)
        for i in range(25):
            Trip.objects.create(
                user=self.user,
                cave_name="Test Trip {}".format(i),
                start=timezone.now() - timezone.timedelta(hours=i),
                end=timezone.now(),
            ).save()

        response = self.client.get(reverse("core:about"))
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

    def test_account_update_page_loads(self):
        """Test that the account update page loads"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("users:account_update"))
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

    def test_user_trip_list_page_loads(self):
        """Test that the user trip list page loads"""
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("log:user", kwargs={"username": self.user.username})
        )
        self.assertEqual(response.status_code, 200)

    def test_user_trip_list_page_loads_with_trips(self):
        """Test that the user trip list page loads with trips"""
        self.client.force_login(self.user)
        for i in range(250):
            t = Trip.objects.create(
                cave_name=f"Test Trip {i}", start=timezone.now(), user=self.user
            )
            t.save()
        response = self.client.get(
            reverse("log:user", kwargs={"username": self.user.username})
        )
        self.assertEqual(response.status_code, 200)

    def test_trip_detail_page_loads(self):
        """Test that the trip detail page loads"""
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("log:trip_detail", kwargs={"pk": self.trip.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_trip_update_page_loads(self):
        """Test that the trip update page loads"""
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("log:trip_update", kwargs={"pk": self.trip.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_trip_list_redirect_page_loads(self):
        """Test that the trip list redirect page loads"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("log:trip_list"), follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, reverse("log:user", kwargs={"username": self.user.username})
        )

    def test_trip_export_page_loads(self):
        """Test that the trip export page loads"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("log:export"))
        self.assertEqual(response.status_code, 200)

    def test_admin_tools_page_loads(self):
        """Test that the admin tools page loads"""
        self.user.is_superuser = True
        self.user.save()
        self.client.force_login(self.user)
        response = self.client.get(reverse("log:admin_tools"))
        self.assertEqual(response.status_code, 200)

    def test_trip_report_detail_page_loads(self):
        """Test that the trip report detail page loads"""
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("log:report_detail", kwargs={"pk": self.report.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_trip_report_update_page_loads(self):
        """Test that the trip report update page loads"""
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("log:report_update", kwargs={"pk": self.report.pk})
        )
        self.assertEqual(response.status_code, 200)

    # TODO: Refactor comments
    # def test_htmx_comment_page_loads(self):
    #     """Test that the HTMX comment page loads"""
    #     self.client.force_login(self.user)
    #     response = self.client.get(
    #         reverse("log:htmx_trip_comment", kwargs={"pk": self.trip.pk})
    #     )
    #     self.assertEqual(response.status_code, 200)

    # def test_htmx_comment_page_loads_with_comments(self):
    #     """Test that the HTMX comment page loads with comments"""
    #     self.client.force_login(self.user)
    #     for i in range(10):
    #         c = Comment.objects.create(
    #             author=self.user,
    #             content_object=self.trip,
    #             content=f"Test Comment {i}"
    #         )
    #         c.save()

    #     response = self.client.get(
    #         reverse("log:htmx_trip_comment", kwargs={"pk": self.trip.pk})
    #     )
    #     self.assertEqual(response.status_code, 200)

    def test_htmx_trip_like_toggle_page_loads(self):
        """Test that the HTMX trip like toggle page loads"""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("log:trip_like_htmx_view", kwargs={"pk": self.trip.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_htmx_trip_like_toggle_page_loads_with_likes(self):
        """Test that the HTMX trip like toggle page loads with likes"""
        self.client.force_login(self.user)
        self.trip.likes.add(self.user)
        response = self.client.post(
            reverse("log:trip_like_htmx_view", kwargs={"pk": self.trip.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_hours_per_month_chart_page_loads(self):
        """Test that the hours per month chart page loads"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("log:charts:hours_per_month"))
        self.assertEqual(response.status_code, 200)

    def test_stats_over_time_chart_page_loads(self):
        """Test that the stats over time chart page loads"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("log:charts:stats_over_time"))
        self.assertEqual(response.status_code, 200)

    def test_trip_types_chart_page_loads(self):
        """Test that the trip types chart page loads"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("log:charts:trip_types"))
        self.assertEqual(response.status_code, 200)

    def test_trip_types_over_time_chart_page_loads(self):
        """Test that the trip types over time chart page loads"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("log:charts:trip_types_time"))
        self.assertEqual(response.status_code, 200)

    def test_statistics_page_loads(self):
        """Test that the statistics page loads"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("log:statistics"))
        self.assertEqual(response.status_code, 200)
