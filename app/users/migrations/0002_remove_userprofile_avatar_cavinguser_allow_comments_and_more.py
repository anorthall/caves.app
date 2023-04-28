# Generated by Django 4.2 on 2023-04-28 14:42

import django_countries.fields
import timezone_field.fields
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0001_squash_all_users"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="userprofile",
            name="avatar",
        ),
        migrations.AddField(
            model_name="cavinguser",
            name="allow_comments",
            field=models.BooleanField(
                default=True,
                help_text="If enabled, other users will be able to comment on your trips and trip reports. Disabling this setting will not delete any existing comments, but will hide them until it is re-enabled.",
                verbose_name="Allow comments on your trips",
            ),
        ),
        migrations.AddField(
            model_name="cavinguser",
            name="allow_friend_email",
            field=models.BooleanField(
                default=False,
                help_text="If enabled, other users will be able to add you as a friend by entering your email address. This will not affect your ability to add other users as friends.",
                verbose_name="Allow friend requests by email",
            ),
        ),
        migrations.AddField(
            model_name="cavinguser",
            name="allow_friend_username",
            field=models.BooleanField(
                default=True,
                help_text="If enabled, other users will be able to add you as a friend by entering your username. This will not affect your ability to add other users as friends.",
                verbose_name="Allow friend requests by username",
            ),
        ),
        migrations.AddField(
            model_name="cavinguser",
            name="bio",
            field=models.TextField(
                blank=True,
                help_text="Information about you that will be displayed on your public profile.",
                verbose_name="biography",
            ),
        ),
        migrations.AddField(
            model_name="cavinguser",
            name="clubs",
            field=models.CharField(
                blank=True,
                help_text="A list of caving clubs or organisations that you are a member of.",
                max_length=50,
            ),
        ),
        migrations.AddField(
            model_name="cavinguser",
            name="country",
            field=django_countries.fields.CountryField(blank=True, max_length=2),
        ),
        migrations.AddField(
            model_name="cavinguser",
            name="friends",
            field=models.ManyToManyField(blank=True, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name="cavinguser",
            name="location",
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name="cavinguser",
            name="page_title",
            field=models.CharField(
                blank=True,
                help_text="A title to display on your profile page (if enabled). If left blank it will use your full name.",
                max_length=50,
            ),
        ),
        migrations.AddField(
            model_name="cavinguser",
            name="privacy",
            field=models.CharField(
                choices=[
                    ("Public", "Anyone"),
                    ("Friends", "Only my friends"),
                    ("Private", "Only me"),
                ],
                default="Private",
                help_text="Who can view your profile?",
                max_length=10,
                verbose_name="Profile privacy",
            ),
        ),
        migrations.AddField(
            model_name="cavinguser",
            name="private_notes",
            field=models.BooleanField(
                default=True,
                help_text="Check this box to prevent your trip notes being displayed on your public profile (if enabled).",
                verbose_name="Keep notes private",
            ),
        ),
        migrations.AddField(
            model_name="cavinguser",
            name="public_statistics",
            field=models.BooleanField(
                default=True,
                help_text="Check this box to show a statistics table on your public profile (if enabled).",
                verbose_name="Show statistics",
            ),
        ),
        migrations.AddField(
            model_name="cavinguser",
            name="timezone",
            field=timezone_field.fields.TimeZoneField(
                choices_display="WITH_GMT_OFFSET",
                default="Europe/London",
                help_text="Timezone to enter and display dates and times in.",
            ),
        ),
        migrations.AddField(
            model_name="cavinguser",
            name="units",
            field=models.CharField(
                choices=[("Metric", "Metric"), ("Imperial", "Imperial")],
                default="Metric",
                help_text="Preferred units of distance.",
                max_length=10,
                verbose_name="Distance units",
            ),
        ),
    ]
