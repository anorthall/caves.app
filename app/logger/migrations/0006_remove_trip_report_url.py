# Generated by Django 4.1.7 on 2023-03-29 22:12

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("logger", "0005_tripreport"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="trip",
            name="report_url",
        ),
    ]