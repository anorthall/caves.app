from django.db import migrations


def copy_profile_and_settings_data_to_user_model(apps, schema_editor):  # pragma: no cover
    """Copy data from UserProfile and UserSettings to CavingUser."""
    CavingUser = apps.get_model("users", "CavingUser")
    for user in CavingUser.objects.all():
        settings = user.settings
        profile = user.profile

        # Profile information
        for friend in profile.friends.all():
            user.friends.add(friend)

        user.location = profile.location
        user.country = profile.country
        user.bio = profile.bio
        user.clubs = profile.clubs
        user.page_title = profile.page_title

        # Settings
        user.units = settings.units
        user.privacy = settings.privacy
        user.allow_friend_username = settings.allow_friend_username
        user.allow_friend_email = settings.allow_friend_email
        user.allow_comments = settings.allow_comments
        user.public_statistics = settings.show_statistics  # Renamed
        user.private_notes = settings.private_notes
        user.timezone = settings.timezone

        profile.save()
        settings.save()
        user.save()


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0002_remove_userprofile_avatar_cavinguser_allow_comments_and_more"),
    ]

    operations = [
        migrations.RunPython(copy_profile_and_settings_data_to_user_model),
    ]
