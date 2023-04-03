# Generated by Django 4.1.7 on 2023-04-03 09:31

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_alter_news_options_news_author"),
    ]

    operations = [
        migrations.AddField(
            model_name="news",
            name="is_published",
            field=models.BooleanField(
                default=True, help_text="Should the news item appear on the site?"
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="news",
            name="posted_at",
            field=models.DateTimeField(
                help_text="If this date is in the future, it will not appear on the site until then."
            ),
        ),
    ]