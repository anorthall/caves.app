# Generated by Django 4.1.7 on 2023-04-22 18:32

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("logger", "0016_comment_comment_logger_comm_content_0ff2fc_idx"),
    ]

    operations = [
        migrations.RenameField(
            model_name="comment",
            old_name="comment",
            new_name="content",
        ),
    ]