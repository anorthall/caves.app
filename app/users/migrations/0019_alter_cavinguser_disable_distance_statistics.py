# Generated by Django 4.2.2 on 2023-06-09 09:56

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0018_cavinguser_disable_distance_statistics"),
    ]

    operations = [
        migrations.AlterField(
            model_name="cavinguser",
            name="disable_distance_statistics",
            field=models.BooleanField(
                default=False,
                help_text="Enabling this option will mean that you will not be prompted to enter distance statistics when you add a trip, and distance statistics will not be displayed on your public profile or statistics page.",
                verbose_name="Disable distance statistics",
            ),
        ),
    ]
