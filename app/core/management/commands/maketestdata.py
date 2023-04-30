import random

import django.db
import factory.random
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from logger.factories import TripFactory
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

    def handle(self, *args, **options):
        # Handle options
        num_users = options["users"]
        num_trips = options["trips"]
        num_friends = options["friends"]

        generate_likes = True
        if options["no_likes"]:
            generate_likes = False

        random.seed(options["seed"])
        factory.random.reseed_random(options["seed"])

        # Generate users, friendships and trips
        user_pks = _generate_users(self, num_users)
        _generate_friendships(self, num_friends, user_pks)
        trips = _generate_trips(self, num_trips, user_pks, generate_likes)

        self.stdout.write(
            f"Done! Generated {len(user_pks)} users and {len(trips)} trips."
        )


def _generate_users(handler, num_users):
    """Generate num_users amount of users"""
    handler.stdout.write(f"Generating {num_users} users...")

    user_pks = []
    for _ in range(num_users):
        try:
            new_user = UserFactory()
        except django.db.utils.IntegrityError as e:
            handler.stderr.write("Error creating user:\n\n")
            handler.stderr.write(f"{e}\n")
            handler.stderr.write(
                "Perhaps you need to delete your database before "
                "generating further test data? Try removing the "
                "dev-data directory and restarting Docker to reset "
                "the development environment."
            )
            handler.stderr.write(f"Aborting with {len(user_pks)} users created.")
            return

        user_pks.append(new_user.pk)

        handler.stdout.write(f"Created user {new_user.email}: {new_user.name}")

    return user_pks


def _generate_trips(handler, num_trips, user_pks=None, with_likes=True):
    """Generate num_trips amount of trips amongst the users specified"""
    if user_pks is None:
        users = list(User.objects.all())
    else:
        users = list(User.objects.filter(pk__in=user_pks, is_active=True))

    handler.stdout.write(f"Generating {num_trips} trips...")
    trips = []
    for _ in range(num_trips):
        trip = TripFactory(user=random.choice(users))
        trips.append(trip)
        handler.stdout.write(
            f"Created trip with PK {trip.pk} for user {trip.user.email}."
        )

        if with_likes:
            _add_likes_to_trip(trip, users)

    return trips


def _generate_friendships(handler, num_friends, user_pks=None):
    """Generate friendships between users"""
    if user_pks is None:
        user_pks = User.objects.all().values_list("pk", flat=True)

    handler.stdout.write("Making friends...")

    # Only use the users passed to us, and only if they are active
    active_users = list(User.objects.filter(pk__in=user_pks, is_active=True))

    # Leave 20% of users without friends
    eligible_friends = random.sample(active_users, int(len(active_users) * 0.8))

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
        _add_friends_to_user(handler, user, eligible_friends_for_user, num_friends)


def _add_friends_to_user(handler, user, eligible_friends, num_friends):
    """Add num_friends amount of friends to the user, from eligible_friends"""
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
    handler.stdout.write(
        f"Added {friends_added} friends (total {num_friends}) for {user.name}."
    )


def _add_likes_to_trip(trip, users):
    """Add likes to a trip"""
    number_of_likes_to_add = random.randint(0, 7)
    users_that_will_like_the_trip = random.sample(users, number_of_likes_to_add)

    for user in users_that_will_like_the_trip:
        trip.likes.add(user)
