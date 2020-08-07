# Generated by Django 2.2.12 on 2020-08-05 14:13
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("activities", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="event",
            name="activity",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="events",
                to="activities.Activity",
            ),
        ),
    ]