import zoneinfo

import pytz
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, tag
from django.urls import reverse

User = get_user_model()


class TestMiddleware(TestCase):
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

    @tag("fast", "middleware")
    def test_timezone_middleware_with_all_timezones(self):
        """
        Test that the timezone middleware does not produce any errors
        when tested with every timezone in pytz and zoneinfo
        """
        self.client.force_login(self.user)

        response = self.client.get(reverse("log:index"))
        self.assertEqual(response.status_code, 200)

        for tz in pytz.all_timezones:
            self.user.timezone = tz
            self.user.save()

            response = self.client.get(reverse("log:index"))
            self.assertEqual(response.status_code, 200)

        for tz in zoneinfo.available_timezones():
            self.user.timezone = tz
            self.user.save()

            response = self.client.get(reverse("log:index"))
            self.assertEqual(response.status_code, 200)
