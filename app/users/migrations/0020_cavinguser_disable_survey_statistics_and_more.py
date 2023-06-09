# Generated by Django 4.2.2 on 2023-06-09 10:24

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0019_alter_cavinguser_disable_distance_statistics"),
    ]

    operations = [
        migrations.AddField(
            model_name="cavinguser",
            name="disable_survey_statistics",
            field=models.BooleanField(
                default=False,
                help_text="Enabling this option will mean that surveying and resurveying distance statistics will not be displayed on your profile.",
                verbose_name="Disable survey statistics",
            ),
        ),
        migrations.AlterField(
            model_name="cavinguser",
            name="disable_distance_statistics",
            field=models.BooleanField(
                default=False,
                help_text="Enabling this option will mean that rope climbed, rope descended, horizontal distance and aid climbing distance statistics will not be displayed on your profile.",
                verbose_name="Disable distance statistics",
            ),
        ),
    ]
