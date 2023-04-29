import django.db
from django.core.management.base import BaseCommand
from logger.factories import TripFactory
from users.factories import UserFactory


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
            "--output",
            type=int,
            default=1,
            help="Verbosity level; 0=minimal output, 1=normal output",
        )

    def handle(self, *args, **options):
        num_users = options["users"]
        num_trips = options["trips"]

        self.stdout.write(
            "Warning: generating large amounts of test data may take a long time!"
        )
        self.stdout.write(f"Generating {num_users} users...")

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

            if options["verbosity"] >= 1:
                self.stdout.write(f"Created user {new_user.email}: {new_user.name}")

        self.stdout.write(f"Generating {num_trips} trips...")
        trips = []
        for _ in range(num_trips):
            trip = TripFactory()
            trips.append(trip)
            if options["verbosity"] >= 1:
                self.stdout.write(
                    f"Created trip with PK {trip.pk} for user {trip.user.email}."
                )

        users_created = len(users)
        trips_created = len(trips)
        self.stdout.write(
            f"Done! Created {users_created} users and {trips_created} trips."
        )
