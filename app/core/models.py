from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse

User = get_user_model()


class News(models.Model):
    title = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    posted_at = models.DateTimeField()
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
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

    def get_absolute_url(self):
        return reverse("core:news_detail", kwargs={"slug": self.slug})


class FAQ(models.Model):
    question = models.CharField(max_length=100)
    answer = models.TextField(help_text="Markdown is supported.")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    # Metadata
    added = models.DateTimeField("added on", auto_now_add=True)
    updated = models.DateTimeField("last updated", auto_now=True)

    class Meta:
        verbose_name = "FAQ"

    def __str__(self):
        return self.question
