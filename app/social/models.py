from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    url = models.URLField("URL", max_length=255)
    read = models.BooleanField(
        default=False, help_text="Has the notification been read by the user?"
    )
    added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message


class FriendRequest(models.Model):
    user_from = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="friend_requests_sent"
    )
    user_to = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="friend_requests_received"
    )
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user_from", "user_to"], name="unique_friend_request"
            )
        ]

    def __str__(self):
        return f"{self.user_from} -> {self.user_to}"
