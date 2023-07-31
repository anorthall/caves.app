# Generated by Django 4.2.3 on 2023-07-29 21:17

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("caves", "0001_initial"),
        ("logger", "0026_alter_trip_cave_location"),
    ]

    operations = [
        migrations.AddField(
            model_name="trip",
            name="entrance",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="trips",
                to="caves.caveentrance",
            ),
        ),
        migrations.AddField(
            model_name="trip",
            name="system",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="trips",
                to="caves.cavesystem",
            ),
        ),
    ]
