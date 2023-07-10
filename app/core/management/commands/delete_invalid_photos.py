from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from logger.models import TripPhoto


class Command(BaseCommand):
    help = "Clear all invalid photos older than the AWS presigned post timeout"

    def handle(self, *args, **options):
        if not settings.AWS_PRESIGNED_EXPIRY:
            self.stdout.write(
                self.style.WARNING(
                    "AWS_PRESIGNED_EXPIRY not set, skipping photo cleanup."
                )
            )
            exit(0)

        # Delete all photos older than the AWS presigned post timeout
        # plus a 60 second margin
        td = timezone.now() - timezone.timedelta(
            seconds=(int(settings.AWS_PRESIGNED_EXPIRY) + 60)
        )

        invalid_photos = TripPhoto.objects.invalid().filter(added__lte=td)

        count = invalid_photos.count()
        invalid_photos.delete()

        self.stdout.write(self.style.SUCCESS(f"Deleted {count} invalid photos."))
