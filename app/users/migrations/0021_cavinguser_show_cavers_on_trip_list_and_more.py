# Generated by Django 4.2.2 on 2023-06-09 11:00

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0020_cavinguser_disable_survey_statistics_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="cavinguser",
            name="show_cavers_on_trip_list",
            field=models.BooleanField(
                default=True,
                help_text="Enabling this option will display a list of cavers who have been on each of your trips on your profile.",
                verbose_name="Show cavers on trip list",
            ),
        ),
        migrations.AlterField(
            model_name="cavinguser",
            name="public_statistics",
            field=models.BooleanField(
                default=True,
                help_text="Check this box to show a statistics table on your profile.",
                verbose_name="Show statistics",
            ),
        ),
    ]
