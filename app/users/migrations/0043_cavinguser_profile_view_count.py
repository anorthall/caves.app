# Generated by Django 4.2 on 2023-12-18 10:27

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0042_remove_cavinguser_private_notes"),
    ]

    operations = [
        migrations.AddField(
            model_name="cavinguser",
            name="profile_view_count",
            field=models.IntegerField(default=0),
        ),
    ]