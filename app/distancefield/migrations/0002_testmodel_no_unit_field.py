# Generated by Django 2.0.6 on 2018-06-26 12:50

import distancefield.fields
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("distancefield", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="testmodel",
            name="no_unit_field",
            field=distancefield.fields.DistanceField(
                decimal_places=6, default="10in", max_digits=14, unit="inch"
            ),
            preserve_default=False,
        ),
    ]
