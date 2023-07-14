# Generated by Django 4.2.3 on 2023-07-13 10:54

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0030_alter_cavinguser_email_comments_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="cavinguser",
            name="has_mod_perms",
            field=models.BooleanField(
                default=False,
                help_text="User has access to moderator level privileges.",
                verbose_name="Moderator privileges",
            ),
        ),
    ]