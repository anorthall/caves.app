# Generated by Django 4.2.1 on 2023-05-26 02:14

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0008_rename_feed_sorting_cavinguser_feed_ordering"),
    ]

    operations = [
        migrations.AlterField(
            model_name="cavinguser",
            name="feed_ordering",
            field=models.CharField(
                choices=[("-added", "Recently added"), ("-start", "Trip date")],
                default="-added",
                max_length=15,
            ),
        ),
    ]