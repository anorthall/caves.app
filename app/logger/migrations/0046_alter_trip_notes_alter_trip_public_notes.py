# Generated by Django 4.2 on 2023-12-18 12:17

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("logger", "0045_add_trip_view_count"),
    ]

    operations = [
        migrations.AlterField(
            model_name="trip",
            name="notes",
            field=models.TextField(
                blank=True,
                help_text="Notes that will only ever be visible to you. Some <a href='https://www.markdownguide.org/basic-syntax/'>Markdown</a> is supported.",
                verbose_name="private notes",
            ),
        ),
        migrations.AlterField(
            model_name="trip",
            name="public_notes",
            field=models.TextField(
                blank=True,
                help_text="These notes will be visible to anyone who can view the trip. Some <a href='https://www.markdownguide.org/basic-syntax/'>Markdown</a> is supported.",
            ),
        ),
    ]