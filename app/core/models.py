from django.db import models
from django.contrib.auth import get_user_model


class News(models.Model):
    title = models.CharField(max_length=100)
    posted_at = models.DateTimeField()
    author = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True)
    content = models.TextField()

    class Meta:
        verbose_name_plural = "news"

    def __str__(self):
        return self.title
