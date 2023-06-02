import random
import sys

import django.db
import factory.random
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from logger.factories import TripFactory, TripReportFactory
from logger.models import Trip
from users.factories import UserFactory

User = get_user_model()


class Command(BaseCommand):
    help = "Generate random test data for development"

    def add_arguments(self, parser):
        parser.add_argument(
            "--users",
            type=int,
            default=25,
            help="Number of users to generate",
        )

        parser.add_argument(
            "--trips",
            type=int,
            default=6000,
            help="Number of trips to generate",
        )

        parser.add_argument(
            "--reports",
            type=int,
            default=-1,
            help="Number of trip reports to generate",
        )

        parser.add_argument(
            "--friends",
            type=int,
            default=6,
            help="Number of friends to add per user",
        )

        parser.add_argument(
            "--seed",
            type=int,
            default=0,
            help="Seed for random number generator",
        )

        parser.add_argument(
            "--no-likes",
            action="store_true",
            help="Do not generate likes for trips",
        )

        parser.add_argument(
            "--no-comments",
            action="store_true",
            help="Do not generate comments for trips or trip reports",
        )

        parser.add_argument(
            "--admin-trips",
            action="store_true",
            help="Generate trips for the admin@caves.app user",
        )

    def handle(self, *args, **options):
        if not settings.DEBUG:
            self.stderr.write("This command is only intended for use in development.")
            sys.exit(1)

        self.options = options

        if options["reports"] < 0:
            options["reports"] = options["trips"] // 10

        if options["seed"] != 0:
            random.seed(options["seed"])
            factory.random.reseed_random(options["seed"])

        # Generate users, friendships and trips
        user_pks = self._generate_users()

        if options["admin_trips"]:
            admin_user = User.objects.get(email="admin@caves.app")
            user_pks.append(admin_user.pk)

        self._generate_friendships(user_pks)
        trips = self._generate_trips(user_pks)
        reports = self._generate_trip_reports(user_pks)

        if options["verbosity"] >= 1:
            self.stdout.write(
                f"Done! Generated {len(user_pks)} users, {len(trips)} "
                f"trips and {len(reports)} reports."
            )

    def __get_active_users(self, user_pks=None):
        """Return a list of active users, optionally from a list of user PKs"""
        if user_pks is None:
            users = list(User.objects.all())
        else:
            users = list(User.objects.filter(pk__in=user_pks, is_active=True))
        return users

    def __find_trip_without_report(self, trips=None):
        if trips is None:
            trips = list(Trip.objects.all())

        trip = None
        while trip is None:
            trip = random.choice(trips)
            if not trip.has_report:
                trip = trip
                break

        return trip

    def _generate_users(self):
        """Generate num_users amount of users"""
        num_users = self.options["users"]
        if self.options["verbosity"] >= 1:
            self.stdout.write(f"Generating {num_users} users...")

        user_pks = []
        for _ in range(num_users):
            try:
                new_user = UserFactory()
            except django.db.utils.IntegrityError as e:
                self.stderr.write("Error creating user:\n\n")
                self.stderr.write(f"{e}\n")
                self.stderr.write(
                    "Perhaps you need to delete your database before "
                    "generating further test data? Try removing the "
                    "data/development directory and restarting Docker to "
                    "reset the development environment."
                )
                self.stderr.write(f"Aborting with {len(user_pks)} users created.")
                sys.exit("Error creating user")

            user_pks.append(new_user.pk)

            if self.options["verbosity"] >= 2:
                self.stdout.write(f"Created user {new_user.email}: {new_user.name}")

        return user_pks

    def _generate_trips(self, user_pks=None):
        """Generate num_trips amount of trips amongst the users specified"""
        num_trips = self.options["trips"]
        if self.options["verbosity"] >= 1:
            self.stdout.write(f"Generating {num_trips} trips...")
        users = self.__get_active_users(user_pks)

        trips = []
        for _ in range(num_trips):
            trip = TripFactory(user=random.choice(users))
            trips.append(trip)

            num_likes, num_comments = 0, 0
            if not self.options["no_likes"]:
                num_likes = self._add_likes_to_trip(trip, users)
            # TODO: Refactor comments
            # if not self.options["no_comments"]:
            #     num_comments = self._add_comments_to_object(trip, users)

            if self.options["verbosity"] >= 2:
                self.stdout.write(
                    f"Created trip with PK {trip.pk} with {num_likes} likes and "
                    f"{num_comments} comments for user {trip.user.email}."
                )

        return trips

    def _generate_trip_reports(self, user_pks=None, with_comments=True):
        """Generate num_reports amount of trip reports amongst the users specified"""
        num_reports = self.options["reports"]
        if self.options["verbosity"] >= 1:
            self.stdout.write(f"Generating {num_reports} reports...")
        users = self.__get_active_users(user_pks)
        user_pks = [user.pk for user in users]

        reports = []
        trips = list(Trip.objects.filter(user__pk__in=user_pks))
        for _ in range(num_reports):
            trip = self.__find_trip_without_report(trips)
            if trip is None:
                break

            report = TripReportFactory(trip=trip, user=trip.user)
            trips.remove(trip)
            reports.append(report)

            num_comments = 0
            # TODO: Refactor comments
            # if with_comments:
            #     num_comments = self._add_comments_to_object(report, users)

            if self.options["verbosity"] >= 2:
                self.stdout.write(
                    f"Created report with PK {report.pk} with {num_comments} "
                    f"comments for user {trip.user.email}."
                )

        return reports

    def _generate_friendships(self, user_pks=None):
        """Generate friendships between users"""
        num_friends = self.options["friends"]
        if self.options["verbosity"] >= 1:
            self.stdout.write(f"Generating {num_friends} friends per user...")

        users = self.__get_active_users(user_pks)

        # Leave 20% of users without friends
        eligible_friends = random.sample(users, int(len(users) * 0.8))

        # Make sure the admin user gets friends, if possible
        try:
            admin_user = User.objects.get(email="admin@caves.app")
            if admin_user not in eligible_friends:
                eligible_friends.append(admin_user)
        except User.DoesNotExist:
            pass

        # Add friends to each user
        for user in eligible_friends:
            eligible_friends_for_user = eligible_friends.copy()
            eligible_friends_for_user.remove(user)
            self._add_friends_to_user(user, eligible_friends_for_user)

    def _add_friends_to_user(self, user, eligible_friends):
        """Add num_friends amount of friends to the user, from eligible_friends"""
        num_friends = self.options["friends"]
        friends_added = 0

        while num_friends > user.friends.count():
            # Try and find a random user to add as a friend
            try:
                random_user = random.choice(eligible_friends)
            except IndexError:
                break

            # Check that the target user does not have more friends than we want
            while random_user.friends.count() >= num_friends:
                try:
                    eligible_friends.remove(random_user)
                    random_user = random.choice(eligible_friends)
                except IndexError:
                    break

            # No more friends are possible, so abort
            if not eligible_friends:
                break

            # Eligible user found, add them as a friend
            user.friends.add(random_user)
            random_user.friends.add(user)
            eligible_friends.remove(random_user)
            friends_added += 1

        num_friends = user.friends.count()
        if self.options["verbosity"] >= 2:
            self.stdout.write(
                f"Added {friends_added} friends (total {num_friends}) for {user.name}."
            )

    def _add_likes_to_trip(self, trip, users):
        """Add likes to a trip"""
        num_likes = random.randint(0, 7)
        users_that_will_like_the_trip = random.sample(users, num_likes)

        for user in users_that_will_like_the_trip:
            trip.likes.add(user)

        return num_likes

    # TODO: Refactor comments
    # def _add_comments_to_object(self, object, users):
    #     """Add comments to an object"""
    #     if self.options["no_comments"]:
    #         return 0

    #     num_comments = random.randint(0, 6)
    #     for _ in range(num_comments):
    #         user = random.choice(users)
    #         CommentFactory(content_object=object, author=user)

    #     return num_comments
