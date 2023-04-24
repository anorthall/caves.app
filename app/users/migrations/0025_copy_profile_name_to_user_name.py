import django.core.validators
from django.db import migrations, models


def copy_profile_name_to_user_name(apps, schema_editor):
    CavingUser = apps.get_model("users", "CavingUser")
    for user in CavingUser.objects.all():
        user.name = user.profile.name
        user.save()


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0024_cavinguser_name"),
    ]

    operations = [
        migrations.RunPython(copy_profile_name_to_user_name),
    ]
