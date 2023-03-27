from django.test import TestCase, Client
from django.utils import timezone
from django.utils.timezone import datetime as dt
from django.contrib.gis.measure import D
from django.contrib.auth import get_user_model
from .models import Trip
from .urls import urlpatterns as trip_urlpatterns


class TripTestCase(TestCase):
    def setUp(self):
        # Reduce log level to avoid 404 error
        import logging

        logger = logging.getLogger("django.request")
        self.previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)

        # Test user to enable trip creation
        user = get_user_model().objects.create_user(
            email="test@test.com",
            username="testusername",
            password="password",
            first_name="Firstname",
            last_name="Lastname",
        )
        user.privacy = get_user_model().PRIVATE
        user.is_active = True
        user.save()

        # Trip with a start and end time
        Trip.objects.create(
            user=user,
            cave_name="Test Cave 1",
            start=dt.fromisoformat("2010-01-01T12:00:00+00:00"),
            end=dt.fromisoformat("2010-01-01T14:00:00+00:00"),
        )

        # Trip with no end time
        Trip.objects.create(
            user=user,
            cave_name="Test Cave 2",
            start=dt.fromisoformat("2010-01-01T13:00:00+00:00"),
        )

        # Create several trips with different privacy settings
        Trip.objects.create(  # Private
            user=user,
            cave_name="Test Cave 3",
            start=dt.fromisoformat("2010-01-01T14:00:00+00:00"),
            privacy=Trip.PRIVATE,
        )
        Trip.objects.create(  # Public
            user=user,
            cave_name="Test Cave 4",
            start=dt.fromisoformat("2010-01-01T15:00:00+00:00"),
            privacy=Trip.PUBLIC,
        )
        Trip.objects.create(  # Default
            user=user,
            cave_name="Test Cave 5",
            start=dt.fromisoformat("2010-01-01T16:00:00+00:00"),
            privacy=Trip.DEFAULT,
        )

        # Create a trip to test tidbits
        Trip.objects.create(
            user=user,
            cave_name="Test Cave 6",
            start=dt.fromisoformat("2010-01-01T17:00:00+00:00"),
            end=dt.fromisoformat("2010-01-01T19:00:00+00:00"),
            vert_dist_down="100m",
            vert_dist_up="200m",
            horizontal_dist="300m",
            surveyed_dist="400m",
            aid_dist="500m",
        )

    def tearDown(self):
        """Reset the log level back to normal"""
        import logging

        logger = logging.getLogger("django.request")
        logger.setLevel(self.previous_level)

    def test_trip_duration_and_duration_str(self):
        """
        Check that trip duration returns a timedelta with the correct value
        Check that trip duration returns None if no end time
        Check that trip duration_str returns a string with the correct value
        """
        trip_with_end = Trip.objects.get(cave_name="Test Cave 1")
        trip_without_end = Trip.objects.get(cave_name="Test Cave 2")

        self.assertNotEqual(trip_with_end.end, None)
        self.assertEqual(trip_with_end.duration, timezone.timedelta(hours=2))

        self.assertEqual(trip_without_end.end, None)
        self.assertEqual(trip_without_end.duration, None)

    def test_trip_duration_str(self):
        """Check that the trip duration string returns the correct value"""
        trip = Trip.objects.get(cave_name="Test Cave 1")
        self.assertEqual(trip.duration_str, "2 hours")

        trip = Trip.objects.get(cave_name="Test Cave 1")  # Cached, grab again
        trip.end = dt.fromisoformat("2010-01-02T13:01:00+00:00")
        self.assertEqual(trip.duration_str, "1 day, 1 hour and 1 minute")

        trip = Trip.objects.get(cave_name="Test Cave 1")  # Cached, grab again
        trip.end = dt.fromisoformat("2010-01-03T14:02:00+00:00")
        self.assertEqual(trip.duration_str, "2 days, 2 hours and 2 minutes")

    def test_has_distances_property(self):
        """Test the Trip.has_distances property"""
        trip = Trip.objects.get(cave_name="Test Cave 6")
        self.assertTrue(trip.has_distances)

        trip = Trip.objects.get(cave_name="Test Cave 1")
        self.assertFalse(trip.has_distances)

    def test_trip_is_private_and_is_public(self):
        """Test the Trip.is_private and Trip.is_public methods"""
        trip_private = Trip.objects.get(cave_name="Test Cave 3")
        trip_public = Trip.objects.get(cave_name="Test Cave 4")
        trip_default = Trip.objects.get(cave_name="Test Cave 5")

        self.assertTrue(trip_private.is_private)
        self.assertFalse(trip_private.is_public)

        self.assertFalse(trip_public.is_private)
        self.assertTrue(trip_public.is_public)

        self.assertTrue(trip_default.is_private)
        self.assertFalse(trip_default.is_public)

    def test_trip_str(self):
        """Test the Trip.__str__ method"""
        trip = Trip.objects.get(cave_name="Test Cave 1")
        self.assertEqual(str(trip), "Test Cave 1")

    def test_trip_get_absolute_url(self):
        """Test the Trip.get_absolute_url method"""
        trip = Trip.objects.get(cave_name="Test Cave 1")
        self.assertEqual(trip.get_absolute_url(), f"/trip/{trip.pk}/")

    def test_tidbits(self):
        """Test the Trip.tidbits property"""
        trip = Trip.objects.get(cave_name="Test Cave 6")
        tidbits = trip.tidbits

        expected_keys = [
            "Descended",
            "Climbed",
            "Distance",
            "Surveyed",
            "Aided",
            "Duration",
        ]

        self.assertEqual(len(tidbits), len(expected_keys))
        from django.utils.html import escape

        for k, v in tidbits:
            self.assertIn(k, expected_keys)
            if k == "Clubs":
                self.assertEqual(v, escape(trip.clubs))
            elif k == "Duration":
                self.assertEqual(v, escape(trip.duration_str))
            elif k == "Expedition":
                self.assertEqual(v, escape(trip.expedition))
            elif k == "Distance":
                self.assertEqual(v, escape(trip.horizontal_dist))
            elif k == "Climbed":
                self.assertEqual(v, escape(trip.vert_dist_up))
            elif k == "Descended":
                self.assertEqual(v, escape(trip.vert_dist_down))
            elif k == "Surveyed":
                self.assertEqual(v, escape(trip.surveyed_dist))
            elif k == "Aided":
                self.assertEqual(v, escape(trip.aid_dist))

    def test_trip_number_property(self):
        """Test the Trip.trip_index class method"""
        trip = Trip.objects.get(cave_name="Test Cave 1")
        trip_index = Trip.trip_index(trip.user)
        self.assertEqual(len(trip_index), 6)
        self.assertEqual(trip_index[trip.pk], 1)

        trip = Trip.objects.get(cave_name="Test Cave 6")
        trip_index = Trip.trip_index(trip.user)
        self.assertEqual(trip_index[trip.pk], 6)

    def test_trip_index(self):
        """Test the Trip.trip_index class method"""
        user = get_user_model().objects.get(username="testusername")
        trip_index = Trip.trip_index(user)
        self.assertEqual(len(trip_index), 6)
        for trip in Trip.objects.all():
            self.assertEqual(trip_index[trip.pk], trip.number)

    def test_stats_for_user(self):
        """Test the Trip.stats_for_user class method"""
        user = get_user_model().objects.get(username="testusername")
        self.assertEqual(user.trips.count(), 6)
        stats = Trip.stats_for_user(user)
        self.assertEqual(stats["trips"], 6)
        self.assertEqual(stats["vert_down"], D(m=100))
        self.assertEqual(stats["vert_up"], D(m=200))
        self.assertEqual(stats["horizontal"], D(m=300))
        self.assertEqual(stats["surveyed"], D(m=400))
        self.assertEqual(stats["aided"], D(m=500))
        self.assertEqual(stats["time"], "4 hours")

    def test_surface_trips_are_not_counted_towards_stats(self):
        """Test that surface trips are not counted towards stats"""
        user = get_user_model().objects.get(username="testusername")
        Trip.objects.create(
            user=user,
            cave_name="Surface Trip",
            start=dt.fromisoformat("2010-01-01T12:00:00+00:00"),
            end=dt.fromisoformat("2010-01-01T14:00:00+00:00"),
            vert_dist_down="100m",
            vert_dist_up="200m",
            horizontal_dist="300m",
            surveyed_dist="400m",
            aid_dist="500m",
            type=Trip.SURFACE,
        )
        stats = Trip.stats_for_user(user)
        self.assertEqual(stats["trips"], 6)
        self.assertEqual(stats["vert_down"], D(m=100))
        self.assertEqual(stats["vert_up"], D(m=200))
        self.assertEqual(stats["horizontal"], D(m=300))
        self.assertEqual(stats["surveyed"], D(m=400))
        self.assertEqual(stats["aided"], D(m=500))
        self.assertEqual(stats["time"], "4 hours")

    def test_stats_for_user_with_no_trips(self):
        """Test the Trip.stats_for_user class method with no trips"""
        user = get_user_model().objects.create_user(
            email="test_no_trips@test.com",
            username="testusername2",
            password="testpassword",
            first_name="Joe",
            last_name="Bloggs",
        )
        stats = Trip.stats_for_user(user)
        self.assertEqual(stats["trips"], 0)
        self.assertEqual(stats["vert_down"], D(m=0))
        self.assertEqual(stats["vert_up"], D(m=0))
        self.assertEqual(stats["horizontal"], D(m=0))
        self.assertEqual(stats["surveyed"], D(m=0))
        self.assertEqual(stats["aided"], D(m=0))
        self.assertEqual(stats["time"], "0")

    def test_next_and_prev_trip_properties(self):
        """Test the Trip.next_trip and Trip.prev_trip properties"""
        trip = Trip.objects.get(cave_name="Test Cave 1")
        self.assertEqual(trip.prev_trip, None)
        self.assertEqual(trip.next_trip.cave_name, "Test Cave 2")
        self.assertEqual(trip.next_trip.number, trip.number + 1)

        trip = Trip.objects.get(cave_name="Test Cave 6")
        self.assertEqual(trip.next_trip, None)
        self.assertEqual(trip.prev_trip.cave_name, "Test Cave 5")
        self.assertEqual(trip.prev_trip.number, trip.number - 1)


class TripIntegrationTests(TestCase):
    def setUp(self):
        # Reduce log level to avoid 404 error
        import logging

        logger = logging.getLogger("django.request")
        self.previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)

        self.client = Client()

        # Create a user
        self.superuser = get_user_model().objects.create_superuser(
            email="super@user.app",
            username="superuser",
            password="testpassword",
            first_name="Joe",
            last_name="Bloggs",
        )
        self.superuser.is_active = True
        self.superuser.save()

        # Create an enabled user
        self.enabled = get_user_model().objects.create_user(
            email="enabled@user.app",
            username="enabled",
            password="testpassword",
            first_name="Joe",
            last_name="Bloggs",
        )
        self.enabled.is_active = True
        self.enabled.save()

        # Create a disabled user
        self.disabled = get_user_model().objects.create_user(
            email="disabled@user.app",
            username="disabled",
            password="testpassword",
            first_name="Joe",
            last_name="Bloggs",
        )
        self.disabled.is_active = False
        self.disabled.save()

        # Create a trip belonging to the superuser
        self.trip = Trip.objects.create(
            user=self.superuser,
            cave_name="Test Cave",
            start=timezone.now() - timezone.timedelta(days=1),
            end=timezone.now(),
        )

    def tearDown(self):
        """Reset the log level back to normal"""
        import logging

        logger = logging.getLogger("django.request")
        logger.setLevel(self.previous_level)

    def test_status_200_on_all_pages(self):
        """Test that all pages return a status code of 200"""
        self.client.login(email="super@user.app", password="testpassword")
        pages = [
            "/",
            f"/trip/{self.trip.pk}/",
            f"/trip/edit/{self.trip.pk}/",
            f"/trip/delete/{self.trip.pk}/",
            "/trip/add/",
            "/trips/",
            "/trips/export/",
            "/about/",
            "/admin-tools/",
        ]
        for page in pages:
            response = self.client.get(page)
            self.assertEqual(response.status_code, 200)

    def test_non_superuser_cannot_access_admin_tools(self):
        """Test that a non-superuser cannot access the admin tools"""
        self.client.login(email="enabled@user.app", password="testpassword")
        response = self.client.get("/admin-tools/")
        self.assertEqual(response.status_code, 404)

    def test_anonymous_user_cannot_access_trip_pages(self):
        """Test that an anonymous user cannot access trip pages"""
        pages = [
            f"/trip/{self.trip.pk}/",
            f"/trip/edit/{self.trip.pk}/",
            f"/trip/delete/{self.trip.pk}/",
            "/trip/add/",
            "/trips/",
            "/trips/export/",
        ]
        for page in pages:
            response = self.client.get(page)
            self.assertIn(response.status_code, [301, 302])
            self.assertEqual(response.url, "/account/login/?next=" + page)

    def test_user_cannot_access_other_users_trips(self):
        """Test that a user cannot access other users trips"""
        self.client.login(email="enabled@user.app", password="testpassword")
        response = self.client.get(f"/trip/{self.trip.pk}/")
        self.assertEqual(response.status_code, 404)

    def test_superuser_can_access_other_users_trips(self):
        """Test that a superuser can access other users trips"""
        self.client.login(email="super@user.app", password="testpassword")
        trip = Trip.objects.create(
            user=self.enabled, cave_name="Test Superuser", start=timezone.now()
        )
        response = self.client.get(f"/trip/{trip.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Superuser")
        self.assertContains(
            response, "Viewing a trip that belongs to " + self.enabled.email
        )

    def test_about_page(self):
        """Test the about page"""
        response = self.client.get("/about/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "<strong>" + str(Trip.objects.all().count()) + "</strong>"
        )
        self.assertContains(
            response,
            "<strong>" + str(get_user_model().objects.all().count()) + "</strong>",
        )

    def test_trip_delete_view(self):
        """Test the trip delete view"""
        self.client.login(email="super@user.app", password="testpassword")
        response = self.client.get(f"/trip/delete/{self.trip.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Cave")
        self.assertContains(response, "Delete trip?")
        self.assertContains(response, "Are you sure you want to delete the above trip?")

    def test_csv_export(self):
        """Test the CSV export"""
        user = self.enabled
        self.client.login(email="enabled@user.app", password="testpassword")

        # Add 100 trips with random data to the user
        from random import random

        trips = []
        for i in range(100):
            trips.append(
                Trip(
                    user=self.enabled,
                    cave_name="Test Cave " + str(i),
                    cave_region=str(random()),
                    cave_country=str(random()),
                    cavers=str(random()),
                    start=timezone.now() - timezone.timedelta(days=1),
                    end=timezone.now(),
                )
            )
        Trip.objects.bulk_create(trips)

        # Get the CSV export
        response = self.client.post("/trips/export/", {"download": "download"})
        timestamp = timezone.now().strftime("%Y-%m-%d-%H%M")
        filename = f"{user.username}-trips-{timestamp}.csv"
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertEqual(
            response["Content-Disposition"], f'attachment; filename="{filename}"'
        )

        # Check the CSV file
        import csv, io

        csv_data = response.content.decode("utf-8")
        reader = csv.reader(io.StringIO(csv_data))

        i = 0
        next(reader)  # Skip the header row
        for trip in trips:
            row = next(reader)
            self.assertEqual(row[1], trip.cave_name)
            self.assertEqual(row[2], trip.cave_region)
            self.assertEqual(row[3], trip.cave_country)
            self.assertEqual(row[9], trip.cavers)
            self.assertEqual(row[5], trip.start.strftime("%Y-%m-%d %H:%M"))
            self.assertEqual(row[6], trip.end.strftime("%Y-%m-%d %H:%M"))
            i += 1

    def test_trip_delete_post_request(self):
        """Test the trip delete post request"""
        self.client.login(email="super@user.app", password="testpassword")
        response = self.client.post(f"/trip/delete/{self.trip.pk}/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/trips/")
        self.assertEqual(Trip.objects.count(), 0)

    def test_trip_list_view(self):
        """Test the trip list view"""
        self.client.login(email="enabled@user.app", password="testpassword")

        # Create 50 trips with randomised names
        from random import random

        trips = []
        for i in range(50):
            trips.append(
                Trip(
                    user=self.enabled,
                    cave_name="Test Cave " + str(random()),
                    start=timezone.now(),
                )
            )
        Trip.objects.bulk_create(trips)

        # Get the trip list page
        response = self.client.get("/trips/")
        self.assertEqual(response.status_code, 200)
        for trip in trips:
            self.assertContains(response, trip.cave_name)

    def test_trip_list_page_only_lists_users_trips(self):
        """Test that the trip list page only lists the users trips"""
        self.client.login(email="enabled@user.app", password="testpassword")
        # Create 10 trips for another user
        from random import random

        other_trips = []
        for i in range(10):
            other_trips.append(
                Trip(
                    user=self.superuser,
                    cave_name="Other User Trip " + str(random()),
                    start=timezone.now(),
                )
            )
        Trip.objects.bulk_create(other_trips)

        # Create 10 trips for the active user
        trips = []
        for i in range(10):
            trips.append(
                Trip(
                    user=self.enabled,
                    cave_name="Test Cave " + str(random()),
                    start=timezone.now(),
                )
            )
        Trip.objects.bulk_create(trips)

        # Get the trip list page
        response = self.client.get("/trips/")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Other User Trip")

        for trip in trips:
            self.assertContains(response, trip.cave_name)

        for trip in other_trips:
            self.assertNotContains(response, trip.cave_name)

    def test_trip_creation_form(self):
        """Test the trip creation form"""
        self.client.login(email="enabled@user.app", password="testpassword")
        response = self.client.get("/trip/add/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Add a trip")
        self.assertContains(response, "Cave name")
        self.assertContains(response, "Cave region")
        self.assertContains(response, "Cave country")
        self.assertContains(response, "Cavers")
        self.assertContains(response, "Notes")
        self.assertContains(response, "Save")

        response = self.client.post(
            "/trip/add/",
            {
                "cave_name": "Test The Form Cave",
                "cave_region": "Test Region",
                "cave_country": "Test Country",
                "type": Trip.SPORT,
                "cavers": "Test Cavers",
                "start": timezone.now(),
                "end": timezone.now() + timezone.timedelta(days=1),
                "privacy": Trip.DEFAULT,
                "notes": "Test Notes",
            },
        )
        trip = Trip.objects.get(cave_name="Test The Form Cave")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"/trip/{trip.pk}/")
        self.assertEqual(trip.cave_name, "Test The Form Cave")
        self.assertEqual(trip.cave_region, "Test Region")
        self.assertEqual(trip.cave_country, "Test Country")
        self.assertEqual(trip.type, Trip.SPORT)
        self.assertEqual(trip.cavers, "Test Cavers")
        self.assertEqual(trip.notes, "Test Notes")
        self.assertEqual(trip.privacy, Trip.DEFAULT)

    def test_trip_update_form(self):
        """Test the trip update form"""
        self.client.login(email="super@user.app", password="testpassword")
        response = self.client.get(f"/trip/edit/{self.trip.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Edit trip")
        self.assertContains(response, "Cave name")
        self.assertContains(response, "Cave region")
        self.assertContains(response, "Cave country")
        self.assertContains(response, "Cavers")
        self.assertContains(response, "Notes")
        self.assertContains(response, "Save")
        self.assertContains(response, self.trip.cave_name)

        response = self.client.post(
            f"/trip/edit/{self.trip.pk}/",
            {
                "cave_name": "Test The Form Cave",
                "cave_region": "Test Region",
                "cave_country": "Test Country",
                "type": Trip.SPORT,
                "cavers": "Test Cavers",
                "start": timezone.now(),
                "end": timezone.now() + timezone.timedelta(days=1),
                "privacy": Trip.DEFAULT,
                "notes": "Test Notes",
            },
        )
        trip = Trip.objects.get(pk=self.trip.pk)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"/trip/{trip.pk}/")
        self.assertEqual(trip.cave_name, "Test The Form Cave")
        self.assertEqual(trip.cave_region, "Test Region")
        self.assertEqual(trip.cave_country, "Test Country")
        self.assertEqual(trip.type, Trip.SPORT)
        self.assertEqual(trip.cavers, "Test Cavers")
        self.assertEqual(trip.notes, "Test Notes")
        self.assertEqual(trip.privacy, Trip.DEFAULT)
