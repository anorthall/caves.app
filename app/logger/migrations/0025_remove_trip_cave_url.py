# Generated by Django 4.2.3 on 2023-07-27 17:02

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("logger", "0024_alter_trip_cave_location"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="trip",
            name="cave_url",
        ),
    ]
