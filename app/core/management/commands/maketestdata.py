import random

import django.db
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from logger.factories import TripFactory
from users.factories import UserFactory

User = get_user_model()

# TODO: Allow configuration of seed
random.seed(0)


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
            "--friends",
            type=int,
            default=6,
            help="Number of friends to add per user",
        )

    def handle(self, *args, **options):  # noqa: C901
        num_users = options["users"]
        num_trips = options["trips"]

        self.stdout.write(
            "Warning: generating large amounts of test data may take a long time!"
        )
        self.stdout.write(f"Generating {num_users} users...")

        # Generate users
        users = []
        for _ in range(num_users):
            try:
                new_user = UserFactory()
            except django.db.utils.IntegrityError as e:
                self.stderr.write("Error creating user:\n\n")
                self.stderr.write(f"{e}\n")
                self.stderr.write(
                    "Perhaps you need to delete your database before "
                    "generating further test data? Try removing the "
                    "dev-data directory and restarting Docker to reset "
                    "the development environment."
                )
                self.stderr.write(f"Aborting with {len(users)} users created.")
                return

            users.append(new_user)

            self.stdout.write(f"Created user {new_user.email}: {new_user.name}")

        # Select users to be friends with each other
        # Leave 20% of users without friends
        self.stdout.write("Making friends...")
        active_users = list(User.objects.filter(is_active=True))
        eligible_friends = random.sample(active_users, int(len(active_users) * 0.8))

        # Make sure the admin user gets friends, if possible
        try:
            admin_user = User.objects.get(email="admin@caves.app")
            if admin_user not in eligible_friends:
                eligible_friends.append(admin_user)
        except User.DoesNotExist:
            pass

        for user in eligible_friends:
            eligible_friends_for_user = eligible_friends.copy()
            eligible_friends_for_user.remove(user)

            while options["friends"] > user.friends.count():
                try:
                    random_user = random.choice(eligible_friends_for_user)
                except IndexError:
                    break

                # Limit the amount of friends users can have to the value
                # given in --friends.
                while random_user.friends.count() >= options["friends"]:
                    try:
                        eligible_friends_for_user.remove(random_user)
                        random_user = random.choice(eligible_friends_for_user)
                    except IndexError:
                        break

                if not eligible_friends_for_user:
                    break

                user.friends.add(random_user)
                random_user.friends.add(user)
                eligible_friends_for_user.remove(random_user)
                self.stdout.write(
                    f"Added {random_user.name} as a friend of {user.name}."
                )

        # Generate trips
        self.stdout.write(f"Generating {num_trips} trips...")
        trips = []
        for _ in range(num_trips):
            trip = TripFactory()
            trips.append(trip)
            self.stdout.write(
                f"Created trip with PK {trip.pk} for user {trip.user.email}."
            )

            number_of_likes = random.randint(0, 7)
            users_to_like = random.sample(users, number_of_likes)
            for user in users_to_like:
                trip.likes.add(user)
                self.stdout.write(
                    f"Added like for trip {trip.pk} by user {user.email}."
                )

        users_created = len(users)
        trips_created = len(trips)
        self.stdout.write(
            f"Done! Created {users_created} users and {trips_created} trips."
        )
