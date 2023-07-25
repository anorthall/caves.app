from django.core.management.base import BaseCommand
from django.utils import timezone
from users.models import CavingUser as User


class Command(BaseCommand):
    help = "Delete all users older than 24 hours where is_active=False"

    def handle(self, *args, **options):
        td = timezone.now() - timezone.timedelta(hours=24)

        users_to_delete = User.objects.filter(
            is_active=False,
            has_verified_email=False,
            date_joined__lte=td,
        )

        count = users_to_delete.count()
        users_to_delete.delete()

        self.stdout.write(self.style.SUCCESS(f"Deleted {count} unverified users."))
