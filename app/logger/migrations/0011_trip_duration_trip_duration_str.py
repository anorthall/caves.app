# Generated by Django 4.1.7 on 2023-04-09 17:37

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("logger", "0010_alter_trip_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="trip",
            name="duration",
            field=models.DurationField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="trip",
            name="duration_str",
            field=models.CharField(blank=True, null=True, max_length=100),
        ),
    ]
