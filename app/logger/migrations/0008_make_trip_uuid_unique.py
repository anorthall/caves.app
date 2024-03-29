# Generated by Django 4.2.1 on 2023-06-04 01:17

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("logger", "0007_generate_trip_uuids"),
    ]

    operations = [
        migrations.AlterField(
            model_name="trip",
            name="uuid",
            field=models.UUIDField(
                default=uuid.uuid4,
                editable=False,
                help_text="A unique identifier for this trip.",
                unique=True,
                verbose_name="UUID",
            ),
        ),
    ]
