# Generated by Django 4.2.3 on 2023-07-10 17:52

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("logger", "0018_alter_tripphoto_photo"),
    ]

    operations = [
        migrations.AddField(
            model_name="tripphoto",
            name="deleted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]