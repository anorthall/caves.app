# Generated by Django 4.2 on 2023-12-19 23:16

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0044_remove_cavinguser_public_statistics"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="cavinguser",
            name="show_cavers_on_trip_list",
        ),
    ]