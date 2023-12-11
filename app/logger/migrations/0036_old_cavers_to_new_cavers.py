# Generated by Django 4.2.6 on 2023-10-31 17:03

from django.db import migrations


def migrate_old_cavers_to_new_cavers(apps, schema_editor):
    """Migrate old, comma separated text field to new ManyToMany field"""
    Trip = apps.get_model("logger", "Trip")
    Caver = apps.get_model("logger", "Caver")

    for trip in Trip.objects.all():
        if not trip.cavers:
            continue

        caver_names = trip.cavers.split(",")
        for caver_name in caver_names:
            caver_name = caver_name.strip()[:39]
            if not caver_name:
                continue

            try:
                caver = Caver.objects.get(name__iexact=caver_name, user=trip.user)
            except Caver.DoesNotExist:
                caver = Caver.objects.create(name=caver_name, user=trip.user)

            trip.cavers_new.add(caver)


class Migration(migrations.Migration):
    dependencies = [
        ("logger", "0035_trip_cavers_new"),
    ]

    operations = [
        migrations.RunPython(migrate_old_cavers_to_new_cavers),
    ]
