from django.db import migrations
from logger.models import Trip


def set_all_duration_fields(apps, schema_editor):
    """Set the duration and duration_str on each trip by calling Trip.save()"""
    for trip in Trip.objects.all():
        if not trip.duration:
            trip.set_duration()
        if not trip.duration_str:
            trip.set_duration_str()
        trip.save()


class Migration(migrations.Migration):
    dependencies = [
        ("logger", "0011_trip_duration_trip_duration_str"),
    ]

    operations = [migrations.RunPython(set_all_duration_fields)]
