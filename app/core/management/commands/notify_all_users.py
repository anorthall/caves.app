from django.core.management.base import BaseCommand
from users.models import CavingUser


class Command(BaseCommand):
    help = "Send a notification to all users"

    def add_arguments(self, parser):
        parser.add_argument(
            "url",
            type=str,
            help="URL that the notification will link to",
        )

        parser.add_argument("message", type=str, nargs="+", help="Message to send")

    def handle(self, *args, **options):
        message = " ".join(options["message"])
        url = options["url"]

        # Confirm that the user wants to send the notification
        print("Are you sure you want to send this notification to all users?\n")
        print(f"Message: {message}")
        print(f"URL: {url}\n\n")
        print("Enter 'yes' to confirm, or anything else to cancel.")

        confirm = input()
        if confirm != "yes":
            self.stdout.write(self.style.WARNING("Notification cancelled!"))
            return

        for user in CavingUser.objects.all():
            user.notify(message, url)

        self.stdout.write(self.style.SUCCESS("Notifications sent!"))
