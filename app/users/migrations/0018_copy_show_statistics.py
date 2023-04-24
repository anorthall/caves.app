from django.db import migrations, models, transaction
from django.db.utils import IntegrityError


def copy_show_statistics_setting(apps, schema_editor):
    CavingUser = apps.get_model("users", "CavingUser")
    for user in CavingUser.objects.all():
        settings = user.settings
        settings.show_statistics = user.profile.show_statistics
        settings.save()


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0017_usersettings_show_statistics"),
    ]

    operations = [
        migrations.RunPython(copy_show_statistics_setting),
    ]
