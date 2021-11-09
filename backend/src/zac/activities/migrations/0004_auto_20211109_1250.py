# Generated by Django 2.2.24 on 2021-11-09 12:50

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("activities", "0003_auto_20211008_1136"),
    ]

    operations = [
        migrations.AlterField(
            model_name="activity",
            name="user_assignee",
            field=models.ForeignKey(
                blank=True,
                help_text="Person responsible for managing this activity.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to=settings.AUTH_USER_MODEL,
                verbose_name="user assignee",
            ),
        ),
    ]
