# Generated by Django 4.2.2 on 2023-06-12 12:56

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("logger", "0015_remove_tripphoto_original_file_name_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="trip",
            name="private_photos",
            field=models.BooleanField(
                default=False,
                help_text="If this is ticked, photos uploaded to this trip will only be visible to you, regardless of who can view the trip.",
                verbose_name="Hide photos from public view?",
            ),
        ),
    ]
