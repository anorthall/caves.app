# Generated by Django 4.1.7 on 2023-03-24 23:32

import distance.fields
from django.db import migrations
import logger.validators


class Migration(migrations.Migration):
    dependencies = [
        ("logger", "0002_trip_aid_dist_units_trip_horizontal_dist_units_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="trip",
            name="aid_dist",
            field=distance.fields.DistanceField(
                blank=True,
                decimal_places=6,
                help_text="Distance covered by aid climbing.",
                max_digits=14,
                null=True,
                unit="m",
                unit_field="aid_dist_units",
                validators=[
                    logger.validators.above_zero_dist_validator,
                    logger.validators.vertical_dist_validator,
                ],
                verbose_name="aid climbing distance",
            ),
        ),
        migrations.AlterField(
            model_name="trip",
            name="horizontal_dist",
            field=distance.fields.DistanceField(
                blank=True,
                decimal_places=6,
                help_text="Horizontal distance covered.",
                max_digits=14,
                null=True,
                unit="m",
                unit_field="horizontal_dist_units",
                validators=[
                    logger.validators.above_zero_dist_validator,
                    logger.validators.horizontal_dist_validator,
                ],
                verbose_name="horizontal distance",
            ),
        ),
        migrations.AlterField(
            model_name="trip",
            name="surveyed_dist",
            field=distance.fields.DistanceField(
                blank=True,
                decimal_places=6,
                help_text="Distance surveyed.",
                max_digits=14,
                null=True,
                unit="m",
                unit_field="surveyed_dist_units",
                validators=[
                    logger.validators.above_zero_dist_validator,
                    logger.validators.horizontal_dist_validator,
                ],
                verbose_name="surveyed distance",
            ),
        ),
        migrations.AlterField(
            model_name="trip",
            name="vert_dist_down",
            field=distance.fields.DistanceField(
                blank=True,
                decimal_places=6,
                help_text="Distance descended on rope.",
                max_digits=14,
                null=True,
                unit="m",
                unit_field="vert_dist_down_units",
                validators=[
                    logger.validators.above_zero_dist_validator,
                    logger.validators.vertical_dist_validator,
                ],
                verbose_name="rope descent distance",
            ),
        ),
        migrations.AlterField(
            model_name="trip",
            name="vert_dist_up",
            field=distance.fields.DistanceField(
                blank=True,
                decimal_places=6,
                help_text="Distance ascended on rope.",
                max_digits=14,
                null=True,
                unit="m",
                unit_field="vert_dist_up_units",
                validators=[
                    logger.validators.above_zero_dist_validator,
                    logger.validators.vertical_dist_validator,
                ],
                verbose_name="rope ascent distance",
            ),
        ),
    ]