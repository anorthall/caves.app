# Generated by Django 4.2.6 on 2023-10-31 17:19

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("logger", "0036_old_cavers_to_new_cavers"),
    ]

    operations = [
        migrations.RenameField(
            model_name="trip",
            old_name="cavers",
            new_name="cavers_old",
        ),
        migrations.RenameField(
            model_name="trip",
            old_name="cavers_new",
            new_name="cavers",
        ),
    ]
