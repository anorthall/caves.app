from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone
from logger.models import TripPhoto


class Command(BaseCommand):
    help = "Clean up invalid and orphaned photos"

    def handle(self, *args, **options):
        if not settings.AWS_PRESIGNED_EXPIRY:
            self.stdout.write(
                self.style.WARNING("AWS_PRESIGNED_EXPIRY not set, skipping photo cleanup.")
            )
            exit(0)

        # Delete all photos older than the AWS presigned post timeout
        # plus a 60 second margin
        td = timezone.now() - timezone.timedelta(seconds=(int(settings.AWS_PRESIGNED_EXPIRY) + 60))

        invalid_photos = TripPhoto.objects.invalid().filter(added__lte=td)

        deleted_count = invalid_photos.count()
        invalid_photos.delete()

        # Mark orphaned photos as deleted
        orphans = TripPhoto.objects.all().filter(
            Q(trip__isnull=True) | Q(user__isnull=True), deleted_at__isnull=True
        )
        orphan_count = orphans.count()
        orphans.update(deleted_at=timezone.now())

        self.stdout.write(
            self.style.SUCCESS(
                f"Deleted {deleted_count} invalid photos and marked "
                f"{orphan_count} orphaned photos as deleted."
            )
        )
