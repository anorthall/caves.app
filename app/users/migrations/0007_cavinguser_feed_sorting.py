# Generated by Django 4.2.1 on 2023-05-26 01:44

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0006_alter_cavinguser_clubs"),
    ]

    operations = [
        migrations.AddField(
            model_name="cavinguser",
            name="feed_sorting",
            field=models.CharField(
                choices=[("-added", "Recently added"), ("-start", "Trip date")],
                default="-added",
                max_length=15,
            ),
        ),
    ]
