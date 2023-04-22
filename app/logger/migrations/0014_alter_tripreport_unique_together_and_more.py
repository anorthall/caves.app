# Generated by Django 4.1.7 on 2023-04-17 20:24

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("logger", "0013_alter_trip_cavers_alter_trip_clubs_and_more"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="tripreport",
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name="tripreport",
            constraint=models.UniqueConstraint(
                fields=("user", "slug"), name="unique_slug_per_user"
            ),
        ),
    ]