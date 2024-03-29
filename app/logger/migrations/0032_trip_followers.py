# Generated by Django 4.2.6 on 2023-10-26 05:54

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("logger", "0031_delete_tripreport"),
    ]

    operations = [
        migrations.AddField(
            model_name="trip",
            name="followers",
            field=models.ManyToManyField(
                blank=True, related_name="followed_trips", to=settings.AUTH_USER_MODEL
            ),
        ),
    ]
