# Generated by Django 4.2.1 on 2023-06-04 01:17

import uuid

from django.db import migrations


def generate_trip_uuids(apps, schema_editor):  # pragma: no cover
    Trip = apps.get_model("logger", "Trip")
    for trip in Trip.objects.all():
        trip.uuid = uuid.uuid4()
        trip.save(update_fields=["uuid"])


class Migration(migrations.Migration):
    dependencies = [
        ("logger", "0006_add_trip_uuid_field_and_update_help_text"),
    ]

    operations = [
        migrations.RunPython(
            generate_trip_uuids, reverse_code=migrations.RunPython.noop
        ),
    ]