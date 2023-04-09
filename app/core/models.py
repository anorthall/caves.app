from django.db import models
from django.contrib.auth import get_user_model


class News(models.Model):
    title = models.CharField(max_length=100)
    posted_at = models.DateTimeField(
        help_text="If this date is in the future, it will not appear on the site until then."
    )
    author = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True)
    content = models.TextField(help_text="Markdown is supported.")
    is_published = models.BooleanField(
        "Publish",
        help_text="News items will not appear on the site unless this box is checked.",
    )

    # Metadata
    added = models.DateTimeField("added on", auto_now_add=True)
    updated = models.DateTimeField("last updated", auto_now=True)

    class Meta:
        verbose_name_plural = "news"

    def __str__(self):
        return self.title


class FAQ(models.Model):
    question = models.CharField(max_length=100)
    answer = models.TextField(help_text="Markdown is supported.")
    author = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True)

    # Metadata
    added = models.DateTimeField("added on", auto_now_add=True)
    updated = models.DateTimeField("last updated", auto_now=True)

    class Meta:
        verbose_name = "FAQ"

    def __str__(self):
        return self.question
