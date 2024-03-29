# Generated by Django 4.2.3 on 2023-07-10 15:47

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0026_alter_notification_user"),
    ]

    operations = [
        migrations.AddField(
            model_name="cavinguser",
            name="disable_stats_over_time",
            field=models.BooleanField(
                default=False,
                help_text="Enabling this option will hide the statistics over time chart on the statistics page.",
                verbose_name="Disable statistics over time chart",
            ),
        ),
    ]
