from django.db import migrations, models, transaction
from django.db.utils import IntegrityError


def copy_settings_data(apps, schema_editor):
    CavingUser = apps.get_model("users", "CavingUser")
    UserSettings = apps.get_model("users", "UserSettings")
    for user in CavingUser.objects.all():
        try:  # Create settings
            with transaction.atomic():
                user.settings = UserSettings.objects.create(user=user)
                user.save()
        except IntegrityError:
            # User already has settings
            pass

        settings = user.settings
        settings.privacy = user.privacy
        settings.units = user.units
        settings.timezone = user.timezone
        settings.private_notes = user.private_notes
        settings.save()


def copy_profile_data(apps, schema_editor):
    CavingUser = apps.get_model("users", "CavingUser")
    UserProfile = apps.get_model("users", "UserProfile")
    for user in CavingUser.objects.all():
        try:  # Create profile
            with transaction.atomic():
                user.profile = UserProfile.objects.create(user=user)
                user.save()
        except IntegrityError:
            # User already has profile
            pass

        profile = user.profile
        profile.name = user.name
        profile.location = user.location
        profile.country = user.country
        profile.bio = user.bio
        profile.clubs = user.clubs
        profile.page_title = user.profile_page_title
        profile.show_statistics = user.show_statistics
        profile.save()


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0012_remove_userprofile_id_remove_usersettings_id_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="usersettings",
            name="profile_page_title",
        ),
        migrations.RemoveField(
            model_name="usersettings",
            name="show_statistics",
        ),
        migrations.AddField(
            model_name="userprofile",
            name="page_title",
            field=models.CharField(
                blank=True,
                help_text="A title to display on your profile page (if enabled). If left blank it will use your full name.",
                max_length=50,
            ),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="show_statistics",
            field=models.BooleanField(
                default=True,
                help_text="Check this box to show a statistics table on your public profile (if enabled).",
                verbose_name="Show statistics",
            ),
        ),
        migrations.RunPython(copy_settings_data),
        migrations.RunPython(copy_profile_data),
    ]
