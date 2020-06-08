# Generated by Django 2.2.12 on 2020-05-15 13:56

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Advice",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "object_url",
                    models.URLField(
                        help_text="URL reference to the object in its API. Together with object_type, the object is understood.",
                        max_length=1000,
                        verbose_name="object URL",
                    ),
                ),
                (
                    "object_type",
                    models.CharField(
                        choices=[("zaak", "Zaak"), ("document", "Zaak")],
                        default="document",
                        max_length=20,
                        verbose_name="object type",
                    ),
                ),
                (
                    "advice",
                    models.TextField(
                        blank=True,
                        help_text="The content of the advice",
                        max_length=1000,
                        verbose_name="advice text",
                    ),
                ),
                (
                    "accord",
                    models.BooleanField(
                        default=False,
                        help_text="Check to indicate you agree with the document(s).",
                        verbose_name="accord",
                    ),
                ),
                (
                    "created",
                    models.DateTimeField(auto_now_add=True, verbose_name="created"),
                ),
                (
                    "user",
                    models.ForeignKey(
                        help_text="User giving the advice",
                        on_delete=django.db.models.deletion.PROTECT,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="user",
                    ),
                ),
            ],
            options={"verbose_name": "advice", "verbose_name_plural": "advices",},
        ),
    ]