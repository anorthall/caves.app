# Generated by Django 4.2.6 on 2023-10-26 05:55

from django.db import migrations


def make_trip_owner_follow_their_trips(apps, schema_editor):
    trip_model = apps.get_model("logger", "Trip")
    for trip in trip_model.objects.all():
        trip.followers.add(trip.user)


class Migration(migrations.Migration):
    dependencies = [
        ("logger", "0032_trip_followers"),
    ]

    operations = [
        migrations.RunPython(
            make_trip_owner_follow_their_trips, reverse_code=migrations.RunPython.noop
        ),
    ]
