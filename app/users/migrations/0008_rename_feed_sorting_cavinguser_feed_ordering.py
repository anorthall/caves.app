# Generated by Django 4.2.1 on 2023-05-26 01:58

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0007_cavinguser_feed_sorting"),
    ]

    operations = [
        migrations.RenameField(
            model_name="cavinguser",
            old_name="feed_sorting",
            new_name="feed_ordering",
        ),
    ]