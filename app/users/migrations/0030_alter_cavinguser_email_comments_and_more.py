# Generated by Django 4.2.3 on 2023-07-12 10:16

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0029_cavinguser_email_comments"),
    ]

    operations = [
        migrations.AlterField(
            model_name="cavinguser",
            name="email_comments",
            field=models.BooleanField(
                default=True,
                help_text="Send an email when another user comments on your trips.",
                verbose_name="Email me new comments",
            ),
        ),
        migrations.AlterField(
            model_name="cavinguser",
            name="email_friend_requests",
            field=models.BooleanField(
                default=True,
                help_text="Send an email when another user adds you as a friend.",
                verbose_name="Email me new friend requests",
            ),
        ),
    ]