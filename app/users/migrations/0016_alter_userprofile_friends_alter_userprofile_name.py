# Generated by Django 4.1.7 on 2023-04-18 18:35

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0015_remove_cavinguser_bio_remove_cavinguser_clubs_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userprofile",
            name="friends",
            field=models.ManyToManyField(blank=True, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name="userprofile",
            name="name",
            field=models.CharField(
                default="Caver",
                help_text="Your name as you would like it to appear on your public profile.",
                max_length=40,
            ),
        ),
    ]
