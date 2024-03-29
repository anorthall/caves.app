# Generated by Django 4.2.6 on 2023-10-31 17:01

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("logger", "0034_caver"),
    ]

    operations = [
        migrations.AddField(
            model_name="trip",
            name="cavers_new",
            field=models.ManyToManyField(
                blank=True,
                help_text="A list of cavers that were on this trip.",
                to="logger.caver",
            ),
        ),
    ]
