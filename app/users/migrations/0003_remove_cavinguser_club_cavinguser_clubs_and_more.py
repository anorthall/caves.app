# Generated by Django 4.1.7 on 2023-03-17 17:44

from django.db import migrations, models
import timezone_field.fields


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0002_cavinguser_privacy"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="cavinguser",
            name="club",
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
        migrations.AlterField(
            model_name="cavinguser",
            name="bio",
            field=models.TextField(
                blank=True,
                help_text="Information about you that will be displayed on your public profile.",
                verbose_name="about me",
            ),
        ),
        migrations.AlterField(
            model_name="cavinguser",
            name="privacy",
            field=models.CharField(
                choices=[("Public", "Public"), ("Private", "Private")],
                default="Private",
                help_text="Whether your profile is public or private.",
                max_length=10,
                verbose_name="Profile privacy",
            ),
        ),
        migrations.AlterField(
            model_name="cavinguser",
            name="timezone",
            field=timezone_field.fields.TimeZoneField(
                choices_display="WITH_GMT_OFFSET",
                default="Europe/London",
                help_text="Timezone to enter/display dates and times in.",
            ),
        ),
        migrations.AlterField(
            model_name="cavinguser",
            name="units",
            field=models.CharField(
                choices=[("Metric", "Metric"), ("Imperial", "Imperial")],
                default="Metric",
                help_text="Units of distance to display/enter data in.",
                max_length=10,
                verbose_name="Distance units",
            ),
        ),
    ]
