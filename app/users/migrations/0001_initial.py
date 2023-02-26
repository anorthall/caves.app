# Generated by Django 4.1.7 on 2023-02-26 10:19

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="CavingUser",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                (
                    "last_login",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="last login"
                    ),
                ),
                (
                    "email",
                    models.EmailField(
                        max_length=255, unique=True, verbose_name="email address"
                    ),
                ),
                ("username", models.SlugField(max_length=30, unique=True)),
                ("first_name", models.CharField(max_length=30)),
                ("last_name", models.CharField(max_length=30)),
                ("location", models.CharField(blank=True, max_length=50)),
                ("bio", models.TextField(blank=True, verbose_name="about me")),
                ("is_active", models.BooleanField(default=True)),
                (
                    "is_admin",
                    models.BooleanField(default=False, verbose_name="administrator"),
                ),
            ],
            options={
                "verbose_name": "user",
            },
        ),
    ]
