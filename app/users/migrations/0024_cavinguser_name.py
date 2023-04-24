# Generated by Django 4.2 on 2023-04-24 08:19

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0023_usersettings_allow_comments_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="cavinguser",
            name="name",
            field=models.CharField(
                default="Caver",
                help_text="Your name as you would like it to appear on your public profile.",
                max_length=25,
                validators=[django.core.validators.MinLengthValidator(3)],
            ),
        ),
    ]