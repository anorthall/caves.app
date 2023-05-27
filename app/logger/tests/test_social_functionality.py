from django.contrib.auth import get_user_model
from django.test import Client, TestCase, tag
from django.urls import reverse
from django.utils import timezone as tz
from django.utils.timezone import timedelta as td

from ..models import Trip, TripReport

User = get_user_model()


@tag("integration", "fast", "social")
class SocialFunctionalityIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.user = User.objects.create_user(
            email="user@caves.app",
            username="user",
            password="password",
            name="User Name",
        )
        self.user.is_active = True
        self.user.privacy = User.PUBLIC
        self.user.save()

        self.user2 = User.objects.create_user(
            email="user2@caves.app",
            username="user2",
            password="password",
            name="User 2 Name",
        )
        self.user2.is_active = True
        self.user2.privacy = User.PUBLIC
        self.user2.save()

        for i in range(1, 200):
            Trip.objects.create(
                cave_name=f"User1 Cave {i}",
                start=tz.now() - td(days=i),
                user=self.user,
                notes="User1 trip notes",
            )

        for i in range(1, 200):
            Trip.objects.create(
                cave_name=f"User2 Cave {i}",
                start=tz.now() - td(days=i),
                user=self.user2,
                notes="User2 trip notes",
            )

    def test_user_profile_page_trip_list(self):
        """Test the trip list on the user profile page"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("log:user", args=[self.user.username]))
        self.assertEqual(response.status_code, 200)

        # Test pagination and that the correct trips are displayed
        for i in range(1, 50):
            self.assertContains(response, f"User1 Cave {i}")
            self.assertNotContains(response, f"User2 Cave {i}")

        for i in range(51, 100):
            self.assertNotContains(response, f"User1 Cave {i}")
            self.assertNotContains(response, f"User2 Cave {i}")

        # Test edit links appear
        for trip in self.user.trips.order_by("-start")[:50]:
            self.assertContains(response, reverse("log:trip_update", args=[trip.pk]))

        # Test the next page
        response = self.client.get(
            reverse("log:user", args=[self.user.username]) + "?page=2",
        )
        self.assertEqual(response.status_code, 200)
        for i in range(51, 100):
            self.assertContains(response, f"User1 Cave {i}")
            self.assertNotContains(response, f"User2 Cave {i}")

    def test_user_profile_page_title(self):
        """Test the user profile page title"""
        self.client.force_login(self.user)
        self.user.page_title = "Test Page Title 123"
        self.user.save()

        response = self.client.get(reverse("log:user", args=[self.user.username]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Page Title 123")

    def test_user_profile_page_bio(self):
        """Test the user profile page bio"""
        self.client.force_login(self.user)
        self.user.bio = "Test bio 123"
        self.user.save()

        response = self.client.get(reverse("log:user", args=[self.user.username]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test bio 123")

    def test_private_trips_do_not_appear_on_profile_page_trip_list(self):
        """Test that private trips do not appear on the user profile page"""
        for trip in self.user.trips:
            trip.privacy = Trip.PRIVATE
            trip.save()

        self.client.force_login(self.user2)
        response = self.client.get(reverse("log:user", args=[self.user.username]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "User1 Cave")

    def test_friend_only_trips_do_not_appear_on_profile_page_trip_list(self):
        """Test that friend only trips do not appear on the user profile page"""
        for trip in self.user.trips:
            trip.privacy = Trip.FRIENDS
            trip.save()

        self.client.force_login(self.user2)
        response = self.client.get(reverse("log:user", args=[self.user.username]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "User1 Cave")

    def test_that_friend_only_trips_appear_to_friends(self):
        """Test that friend only trips appear on the user profile page to friends"""
        for trip in self.user.trips:
            trip.privacy = Trip.FRIENDS
            trip.save()

        self.user.friends.add(self.user2)
        self.user2.friends.add(self.user)

        self.client.force_login(self.user2)
        response = self.client.get(reverse("log:user", args=[self.user.username]))
        self.assertEqual(response.status_code, 200)

        for trip in self.user.trips.order_by("-start")[:50]:
            self.assertContains(response, trip.cave_name)

    def test_that_private_trips_do_not_appear_in_the_trip_feed(self):
        """Test that private trips do not appear in the trip feed"""
        self.client.force_login(self.user2)
        self.user.friends.add(self.user2)
        self.user2.friends.add(self.user)

        # Delete all user2 trips so they don't appear in the feed
        # and block user1 trips from appearing
        for trip in self.user2.trips:
            trip.delete()

        # First set the trips to public and verify they do appear in the
        # feed, otherwise if sorting is broken the test will pass even if
        # private trips are appearing in the feed
        for trip in self.user.trips:
            trip.privacy = Trip.PUBLIC
            trip.save()

        response = self.client.get(reverse("log:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "User1 Cave")

        # Now set the trips to private and verify they do not appear in the feed
        for trip in self.user.trips:
            trip.privacy = Trip.PRIVATE
            trip.save()

        response = self.client.get(reverse("log:index"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "User1 Cave")

    def test_trip_detail_page_with_various_privacy_settings(self):
        """Test the trip detail page with various privacy settings"""
        trip = self.user.trips.first()
        trip.privacy = Trip.PUBLIC
        trip.save()

        self.client.force_login(self.user2)
        response = self.client.get(reverse("log:trip_detail", args=[trip.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, trip.cave_name)

        trip.privacy = Trip.FRIENDS
        trip.save()
        response = self.client.get(reverse("log:trip_detail", args=[trip.pk]))
        self.assertEqual(response.status_code, 403)

        self.user.friends.add(self.user2)
        self.user2.friends.add(self.user)
        response = self.client.get(reverse("log:trip_detail", args=[trip.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, trip.cave_name)

        trip.privacy = Trip.PRIVATE
        trip.save()
        response = self.client.get(reverse("log:trip_detail", args=[trip.pk]))
        self.assertEqual(response.status_code, 403)

        trip.privacy = Trip.DEFAULT
        trip.save()
        self.user.privacy = User.PRIVATE
        self.user.save()
        response = self.client.get(reverse("log:trip_detail", args=[trip.pk]))
        self.assertEqual(response.status_code, 403)

        self.user.privacy = User.PUBLIC
        self.user.save()
        response = self.client.get(reverse("log:trip_detail", args=[trip.pk]))
        self.assertEqual(response.status_code, 200)

        self.user.privacy = User.FRIENDS
        self.user.save()
        response = self.client.get(reverse("log:trip_detail", args=[trip.pk]))
        self.assertContains(response, trip.cave_name)

        self.user.privacy = User.PUBLIC
        self.user.save()
        response = self.client.get(reverse("log:trip_detail", args=[trip.pk]))
        self.assertContains(response, trip.cave_name)

        self.client.logout()
        response = self.client.get(reverse("log:trip_detail", args=[trip.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, trip.cave_name)

        self.user.privacy = User.FRIENDS
        self.user.save()
        response = self.client.get(reverse("log:trip_detail", args=[trip.pk]))
        self.assertEqual(response.status_code, 403)

        self.user.privacy = User.PRIVATE
        self.user.save()
        response = self.client.get(reverse("log:trip_detail", args=[trip.pk]))
        self.assertEqual(response.status_code, 403)

    def test_user_profile_page_with_various_privacy_settings(self):
        """Test the user profile page with various privacy settings"""
        self.client.force_login(self.user2)
        response = self.client.get(reverse("log:user", args=[self.user.username]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.username)

        self.user.privacy = User.PRIVATE
        self.user.save()
        response = self.client.get(reverse("log:user", args=[self.user.username]))
        self.assertEqual(response.status_code, 403)

        self.user.privacy = User.FRIENDS
        self.user.save()
        response = self.client.get(reverse("log:user", args=[self.user.username]))
        self.assertEqual(response.status_code, 403)

        self.user.friends.add(self.user2)
        self.user2.friends.add(self.user)
        response = self.client.get(reverse("log:user", args=[self.user.username]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.username)

        self.user.privacy = User.PUBLIC
        self.user.save()
        response = self.client.get(reverse("log:user", args=[self.user.username]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.username)

        self.client.logout()
        self.user.privacy = User.PRIVATE
        self.user.save()
        response = self.client.get(reverse("log:user", args=[self.user.username]))
        self.assertEqual(response.status_code, 403)

        self.user.privacy = User.FRIENDS
        self.user.save()
        response = self.client.get(reverse("log:user", args=[self.user.username]))
        self.assertEqual(response.status_code, 403)

        self.user.privacy = User.PUBLIC
        self.user.save()
        response = self.client.get(reverse("log:user", args=[self.user.username]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.username)

    def test_sidebar_displays_properly_when_viewing_another_users_trip(self):
        """Test that the sidebar displays properly when viewing another user's trip"""
        self.client.force_login(self.user2)
        trip = Trip.objects.filter(user=self.user).first()
        response = self.client.get(reverse("log:trip_detail", args=[trip.pk]))
        self.assertContains(response, trip.cave_name)
        self.assertContains(response, f"Trip by {self.user.name}")
        self.assertContains(response, "View profile")
        self.assertContains(response, "View this trip")
        self.assertContains(response, "Add as friend")

        self.assertNotContains(response, reverse("log:trip_update", args=[trip.pk]))
        self.assertNotContains(response, reverse("log:trip_delete", args=[trip.pk]))
        self.assertNotContains(response, reverse("log:report_create", args=[trip.pk]))

    def test_add_as_friend_link_does_not_appear_when_disabled(self):
        """Test that the add as friend link does not appear when disabled"""
        self.user.allow_friend_username = False
        self.user.save()

        self.client.force_login(self.user2)
        trip = Trip.objects.filter(user=self.user).first()
        response = self.client.get(reverse("log:trip_detail", args=[trip.pk]))
        self.assertNotContains(response, "Add as friend")
        self.assertNotContains(response, reverse("users:friend_add"))

    def test_add_as_friend_link_does_not_appear_when_already_friends(self):
        """Test that the add as friend link does not appear when already friends"""
        self.user.friends.add(self.user2)
        self.user2.friends.add(self.user)

        self.client.force_login(self.user2)
        trip = Trip.objects.filter(user=self.user).first()
        response = self.client.get(reverse("log:trip_detail", args=[trip.pk]))
        self.assertNotContains(response, "Add as friend")
        self.assertNotContains(response, reverse("users:friend_add"))

    # TODO: Refactor comments
    # def test_comments_appear_on_trip_detail_page(self):
    #     """Test that comments appear on the trip detail page"""
    #     trip = Trip.objects.filter(user=self.user).first()
    #     comment = Comment.objects.create(
    #         author=self.user,
    #         content_object=trip,
    #         content="Test comment",
    #     )
    #     response = self.client.get(reverse("log:trip_detail", args=[trip.pk]))
    #     self.assertContains(response, comment.content)

    # def test_comments_do_not_appear_on_trip_detail_page_when_disabled(self):
    #     """Test that comments do not appear on the trip detail page when disabled"""
    #     self.user.allow_comments = False
    #     self.user.save()

    #     trip = Trip.objects.filter(user=self.user).first()
    #     comment = Comment.objects.create(
    #         author=self.user2,
    #         content_object=trip,
    #         content="Test comment",
    #     )
    #     response = self.client.get(reverse("log:trip_detail", args=[trip.pk]))
    #     self.assertNotContains(response, comment.content)

    # def test_comments_appear_on_trip_report_page(self):
    #     """Test that comments appear on the trip report page"""
    #     report = TripReport.objects.create(
    #         user=self.user,
    #         trip=Trip.objects.filter(user=self.user).first(),
    #         title="Test report",
    #         content="Test report content",
    #         pub_date=tz.now().date(),
    #     )
    #     comment = Comment.objects.create(
    #         author=self.user,
    #         content_object=report,
    #         content="Test comment",
    #     )
    #     response = self.client.get(reverse("log:report_detail", args=[report.pk]))
    #     self.assertContains(response, comment.content)

    # def test_comments_do_not_appear_on_trip_report_page_when_disabled(self):
    #     """Test that comments do not appear on the trip report page when disabled"""
    #     self.user.allow_comments = False
    #     self.user.save()

    #     report = TripReport.objects.create(
    #         user=self.user,
    #         trip=Trip.objects.filter(user=self.user).first(),
    #         title="Test report",
    #         content="Test report content",
    #         pub_date=tz.now().date(),
    #     )
    #     comment = Comment.objects.create(
    #         author=self.user,
    #         content_object=report,
    #         content="Test comment",
    #     )
    #     response = self.client.get(reverse("log:report_detail", args=[report.pk]))
    #     self.assertNotContains(response, comment.content)

    # def test_user_profile_is_linked_on_comments(self):
    #     """Test that the user profile is linked on comments"""
    #     trip = Trip.objects.filter(user=self.user).first()
    #     comment = Comment.objects.create(
    #         author=self.user,
    #         content_object=trip,
    #         content="Test comment",
    #     )
    #     response = self.client.get(reverse("log:trip_detail", args=[trip.pk]))
    #     self.assertContains(response, self.user.name)
    #     self.assertContains(response, comment.content)
    #     self.assertContains(response, reverse("log:user", args=[self.user.username]))

    # def test_user_profile_is_not_linked_on_comments_when_private(self):
    #     """Test that the user profile is not linked on comments when private"""
    #     self.user.privacy = User.PRIVATE
    #     self.user.save()

    #     trip = Trip.objects.filter(user=self.user).first()
    #     trip.privacy = Trip.PUBLIC
    #     trip.save()

    #     comment = Comment.objects.create(
    #         author=self.user,
    #         content_object=trip,
    #         content="Test comment",
    #     )
    #     response = self.client.get(reverse("log:trip_detail", args=[trip.pk]))
    #     self.assertContains(response, self.user.name)
    #     self.assertContains(response, comment.content)
    #   self.assertNotContains(response, reverse("log:user", args=[self.user.username]))

    def test_trip_report_link_appears_in_sidebar_for_other_users(self):
        """Test that the trip report link appears in the sidebar for other users"""
        trip = Trip.objects.filter(user=self.user).first()
        report = TripReport.objects.create(
            user=self.user,
            trip=trip,
            title="Test report",
            content="Test report content",
            pub_date=tz.now().date(),
        )
        response = self.client.get(reverse("log:trip_detail", args=[trip.pk]))
        self.assertContains(response, reverse("log:report_detail", args=[report.pk]))

    def test_trip_report_link_does_not_appear_in_sidebar_when_private(self):
        """Test that the trip report link does not appear in the sidebar when private"""
        trip = Trip.objects.filter(user=self.user).first()

        report = TripReport.objects.create(
            user=self.user,
            trip=trip,
            title="Test report",
            content="Test report content",
            pub_date=tz.now().date(),
            privacy=TripReport.PRIVATE,
        )
        response = self.client.get(reverse("log:trip_detail", args=[trip.pk]))
        self.assertNotContains(response, reverse("log:report_detail", args=[report.pk]))

    # TODO: Refactor comments
    # def test_add_comment_via_post_request(self):
    #     """Test that a comment can be added via a POST request"""
    #     trip = Trip.objects.filter(user=self.user).first()
    #     self.client.force_login(self.user)

    #     response = self.client.post(
    #         reverse("log:comment_add"),
    #         {
    #             "content": "Test comment",
    #             "type": "trip",
    #             "pk": trip.pk,
    #         },
    #         follow=True,
    #     )
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(Comment.objects.count(), 1)
    #     self.assertContains(response, "Test comment")

    # def test_add_comment_via_post_request_to_object_the_user_cannot_view(self):
    #     """Test that a comment cannot be added to an object the user cannot view"""
    #     trip = Trip.objects.filter(user=self.user).first()
    #     self.client.force_login(self.user2)

    #     trip.privacy = Trip.PRIVATE
    #     trip.save()

    #     self.client.post(
    #         reverse("log:comment_add"),
    #         {
    #             "content": "Test comment",
    #             "type": "trip",
    #             "pk": trip.pk,
    #         },
    #     )
    #     self.assertEqual(Comment.objects.count(), 0)

    # def test_add_comment_via_post_request_when_not_logged_in(self):
    #     """Test that the comment view does not load when not logged in"""
    #     trip = Trip.objects.filter(user=self.user).first()
    #     self.client.post(
    #         reverse("log:comment_add"),
    #         {
    #             "content": "Test comment",
    #             "type": "trip",
    #             "pk": trip.pk,
    #         },
    #     )
    #     self.assertEqual(Comment.objects.count(), 0)

    # def test_delete_comment(self):
    #     """Test that a comment can be deleted"""
    #     trip = Trip.objects.filter(user=self.user).first()
    #     comment = Comment.objects.create(
    #         author=self.user,
    #         content_object=trip,
    #         content="Test comment",
    #     )
    #     self.client.force_login(self.user)

    #     response = self.client.post(
    #         reverse("log:comment_delete", args=[comment.pk]),
    #         follow=True,
    #     )
    #     self.assertEqual(response.status_code, 200)
    #     self.assertContains(response, "The comment has been deleted")
    #     self.assertEqual(Comment.objects.count(), 0)

    # def test_delete_comment_that_does_not_belong_to_the_user(self):
    #     """Test that a comment cannot be deleted if it does not belong to the user"""
    #     trip = Trip.objects.filter(user=self.user2).first()
    #     comment = Comment.objects.create(
    #         author=self.user2,
    #         content_object=trip,
    #         content="Test comment",
    #     )
    #     self.client.force_login(self.user)

    #     response = self.client.post(
    #         reverse("log:comment_delete", args=[comment.pk]),
    #     )
    #     self.assertEqual(response.status_code, 403)
    #     self.assertEqual(Comment.objects.count(), 1)

    def test_htmx_like_view_on_an_object_the_user_cannot_view(self):
        """Test that the HTMX like view respects privacy"""
        trip = Trip.objects.filter(user=self.user).first()
        self.client.force_login(self.user2)

        trip.privacy = Trip.PRIVATE
        trip.save()

        response = self.client.post(
            reverse("log:trip_like_htmx_view", args=[trip.pk]),
        )
        self.assertEqual(response.status_code, 403)

    # TODO: Refactor comments
    # def test_htmx_comment_view_on_an_object_the_user_cannot_view(self):
    #     """Test that the HTMX comment view respects privacy"""
    #     trip = Trip.objects.filter(user=self.user).first()
    #     self.client.force_login(self.user2)

    #     trip.privacy = Trip.PRIVATE
    #     trip.save()

    #     response = self.client.get(
    #         reverse("log:htmx_trip_comment", args=[trip.pk]),
    #     )
    #     self.assertEqual(response.status_code, 403)

    # def test_comments_send_a_notification_when_posted(self):
    #     """Test that a notification is sent when a comment is posted"""
    #     trip = Trip.objects.filter(user=self.user).first()
    #     self.client.force_login(self.user2)

    #     response = self.client.post(
    #         reverse("log:comment_add"),
    #         {
    #             "content": "Test comment",
    #             "type": "trip",
    #             "pk": trip.pk,
    #         },
    #         follow=True,
    #     )
    #     self.assertEqual(response.status_code, 200)

    #     self.client.force_login(self.user)
    #     self.assertEqual(Notification.objects.count(), 1)
    #     self.assertEqual(Notification.objects.first().user, self.user)
    #     self.assertEqual(Notification.objects.first().url, trip.get_absolute_url())

    #     response = self.client.get(reverse("log:index"))
    #     self.assertContains(response, f"{self.user2} commented on your trip")

    def test_notification_redirect_view_as_invalid_user(self):
        """Test that the notification redirect view returns a 403 for an invalid user"""
        self.client.force_login(self.user2)
        notification = self.user.notify("Test notification", "/")
        response = self.client.get(
            reverse("users:notification", args=[notification.pk]),
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(notification.read, False)

    # TODO: Refactor comments
    # def test_adding_comment_to_trip_report(self):
    #     """Test that a comment can be added to a trip report"""
    #     trip = Trip.objects.filter(user=self.user).first()
    #     report = TripReport.objects.create(
    #         user=self.user,
    #         trip=trip,
    #         title="Test report",
    #         content="Test report content",
    #         pub_date=tz.now().date(),
    #     )
    #     self.client.force_login(self.user)

    #     response = self.client.post(
    #         reverse("log:comment_add"),
    #         {
    #             "content": "Test comment",
    #             "type": "tripreport",
    #             "pk": report.pk,
    #         },
    #         follow=True,
    #     )
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(Comment.objects.count(), 1)
    #     self.assertContains(response, "Test comment")

    # def test_adding_comment_to_invalid_object_type(self):
    #     """Test that a comment cannot be added to an invalid object type"""
    #     trip = Trip.objects.filter(user=self.user).first()
    #     self.client.force_login(self.user)

    #     response = self.client.post(
    #         reverse("log:comment_add"),
    #         {
    #             "content": "Test comment",
    #             "type": "invalid",
    #             "pk": trip.pk,
    #         },
    #     )
    #     self.assertEqual(Comment.objects.count(), 0)
    #     self.assertEqual(response.url, reverse("log:index"))

    # def test_adding_comment_with_no_content(self):
    #     """Test that a comment cannot be added with no content"""
    #     trip = Trip.objects.filter(user=self.user).first()
    #     self.client.force_login(self.user)

    #     response = self.client.post(
    #         reverse("log:comment_add"),
    #         {
    #             "content": "",
    #             "type": "trip",
    #             "pk": trip.pk,
    #         },
    #         follow=True,
    #     )
    #     self.assertContains(response, "This field is required.")
    #     self.assertEqual(Comment.objects.count(), 0)

    # def test_adding_comment_with_too_much_content(self):
    #     """Test that a comment cannot be added with too much content"""
    #     trip = Trip.objects.filter(user=self.user).first()
    #     self.client.force_login(self.user)

    #     self.client.post(
    #         reverse("log:comment_add"),
    #         {
    #             "content": "x" * 4000,
    #             "type": "trip",
    #             "pk": trip.pk,
    #         },
    #     )
    #     self.assertEqual(Comment.objects.count(), 0)

    # def test_adding_comment_on_an_object_that_does_not_exist(self):
    #     """Test that a comment cannot be added to an object that does not exist"""
    #     self.client.force_login(self.user)

    #     self.client.post(
    #         reverse("log:comment_add"),
    #         {
    #             "content": "Test comment",
    #             "type": "trip",
    #             "pk": 999999999999,
    #         },
    #     )
    #     self.assertEqual(Comment.objects.count(), 0)

    # def test_adding_comment_on_an_object_where_the_user_disallows_comments(self):
    #     """Test users cannot comment where the user disallows comments"""
    #     self.user.allow_comments = False
    #     self.user.save()
    #     trip = Trip.objects.filter(user=self.user).first()
    #     self.client.force_login(self.user2)

    #     self.client.post(
    #         reverse("log:comment_add"),
    #         {
    #             "content": "Test comment",
    #             "type": "trip",
    #             "pk": trip.pk,
    #         },
    #         follow=True,
    #     )
    #     self.assertEqual(Comment.objects.count(), 0)

    def test_trip_report_detail_page_with_various_privacy_settings(self):
        """Test that the trip report detail page respects privacy settings"""
        trip = Trip.objects.filter(user=self.user).first()
        report = TripReport.objects.create(
            user=self.user,
            trip=trip,
            title="Test report",
            content="Test report content",
            pub_date=tz.now().date(),
        )
        self.client.force_login(self.user2)

        report.privacy = TripReport.PRIVATE
        report.save()
        response = self.client.get(
            reverse("log:report_detail", args=[report.pk]),
        )
        self.assertEqual(response.status_code, 403)

        report.privacy = TripReport.FRIENDS
        report.save()
        response = self.client.get(
            reverse("log:report_detail", args=[report.pk]),
        )
        self.assertEqual(response.status_code, 403)

        self.user.friends.add(self.user2)
        self.user2.friends.add(self.user)
        response = self.client.get(
            reverse("log:report_detail", args=[report.pk]),
        )
        self.assertEqual(response.status_code, 200)

        report.privacy = TripReport.PUBLIC
        report.save()
        response = self.client.get(
            reverse("log:report_detail", args=[report.pk]),
        )
        self.assertEqual(response.status_code, 200)

        report.privacy = TripReport.DEFAULT
        report.save()
        trip.privacy = Trip.FRIENDS
        trip.save()
        response = self.client.get(
            reverse("log:report_detail", args=[report.pk]),
        )
        self.assertEqual(response.status_code, 200)

        trip.privacy = Trip.PRIVATE
        trip.save()
        response = self.client.get(
            reverse("log:report_detail", args=[report.pk]),
        )
        self.assertEqual(response.status_code, 403)

        trip.privacy = Trip.PUBLIC
        trip.save()
        response = self.client.get(
            reverse("log:report_detail", args=[report.pk]),
        )
        self.assertEqual(response.status_code, 200)
