# Generated by Django 4.2.1 on 2023-06-02 00:05
import uuid

from django.db import migrations, models


def gen_uuid(apps, schema_editor):  # pragma: no cover
    User = apps.get_model("users", "CavingUser")
    for user in User.objects.all():
        user.uuid = uuid.uuid4()
        user.save(update_fields=["uuid"])


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0012_cavinguser_add_uuid"),
    ]

    operations = [
        migrations.RunPython(gen_uuid, reverse_code=migrations.RunPython.noop),
    ]
