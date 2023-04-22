# Generated by Django 4.1.7 on 2023-04-18 13:10

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0011_usersettings_userprofile"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="userprofile",
            name="id",
        ),
        migrations.RemoveField(
            model_name="usersettings",
            name="id",
        ),
        migrations.AlterField(
            model_name="userprofile",
            name="user",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                primary_key=True,
                related_name="profile",
                serialize=False,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="usersettings",
            name="user",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                primary_key=True,
                related_name="settings",
                serialize=False,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]