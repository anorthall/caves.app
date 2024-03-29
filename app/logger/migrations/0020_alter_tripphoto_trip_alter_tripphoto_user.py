# Generated by Django 4.2.3 on 2023-07-10 18:07

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("logger", "0019_tripphoto_deleted_at"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tripphoto",
            name="trip",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="photos",
                to="logger.trip",
            ),
        ),
        migrations.AlterField(
            model_name="tripphoto",
            name="user",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
