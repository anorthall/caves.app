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
