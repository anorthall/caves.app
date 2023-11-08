# Generated by Django 4.2.6 on 2023-10-26 10:15

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0035_notification_trip_notification_type_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="cavinguser",
            name="email_comments",
            field=models.BooleanField(
                default=True,
                help_text="Send an email when another user comments on a trip you are following.",
                verbose_name="Email me new comments",
            ),
        ),
    ]