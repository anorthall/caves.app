# Generated by Django 4.2 on 2023-12-19 10:04

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0043_cavinguser_profile_view_count"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="cavinguser",
            name="public_statistics",
        ),
    ]
